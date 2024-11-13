/**
 * This is the main entrypoint to your Probot app
 * @param {import('probot').Probot} app
 */

import {sendRepo} from './components/sendRepo.js';
import {sendRatings} from './components/sendRatings.js';
import axios from "axios";


export default (app) => {

	app.on("installation_repositories.added", async (context) => {
		const {repositories_added} = context.payload;
		console.log('Payload:', context.payload);

		try {
			for (const repo of repositories_added) {
				// Extract owner and repo name from full_name
				const [ownerName, repoName] = repo.full_name.split('/');

				// Fetch the full repository data
				const {data: fullRepo} = await context.octokit.repos.get({
					owner: ownerName,
					repo: repoName,
				});

				// Optionally, you can create an issue or perform other actions here
				await context.octokit.issues.create({
					owner: ownerName,
					repo: repoName,
					title: 'Hello!',
					body: 'hi',
				});

				// Pass the full repository object and context to sendRepo
				const data = await sendRepo(fullRepo, context);

				if (!data) {
					console.error(`sendRepo returned null for ${ownerName}/${repoName}. Skipping Axios POST.`);
					continue; // Skip sending to Flask if data is invalid
				}

				try {
					const flaskResponse = await axios.post('http://localhost:5000/initialization', data, {
						headers: {
							'Content-Type': 'application/json',
						},
					});
					if (flaskResponse.status !== 200) {
						throw new Error(`Failed to send data to Flask backend: ${flaskResponse.status} ${flaskResponse.statusText}`);
					}
					console.log('Repo info sent to Flask backend successfully.');
				} catch (error) {
					console.error('Error while sending repo info:', error);
				}
			}
		} catch (error) {
			console.error('Failed to process repositories:', error);
		}
	});


// Handler for issues.opened event
	app.on('issues.opened', async (context) => {
		const issue = context.payload.issue;
		const repository = context.payload.repository;

		console.log(`Issue #${issue.number} opened in repository ${repository.full_name}`);

		// Existing logic for handling issue comments
		const issueBody = issue.body;
		const issueAuthor = issue.user;
		if (issueAuthor.type === 'Bot') {
			console.log(`Issue #${issue.number} opened by a bot (${issueAuthor.login}). Ignoring.`);
			return; // Exit early if the issue was opened by a bot
		}

		let issueCommentBody = 'Thank you for opening this issue!';
		if (issueBody) {
			const imageRegex = /https?:\/\/[^\s)\]]+/g;
			const imageUrls = issueBody.match(imageRegex);

			if (imageUrls) {
				issueCommentBody += ' I found the following images in the issue description:';
				imageUrls.forEach((imageUrl) => {
					issueCommentBody += `\n\n![Image](${imageUrl})`;
				});
			} else {
				issueCommentBody += ' I did not find any images in the issue description.';
			}

			try {
				// Check if the bot already commented
				const comments = await context.octokit.issues.listComments(context.issue());
				const botComment = comments.data.find(
					(comment) => comment.user.type === 'Bot' && comment.body.includes('I found the following images')
				);

				if (botComment) {
					const updatedCommentBody = 'EDIT: The bug report was updated.\n\n' + issueCommentBody;

					console.log('Editing comment with ID:', botComment.id);
					await context.octokit.issues.updateComment({
						...context.issue(),
						comment_id: botComment.id,
						body: updatedCommentBody,
					});
				} else {
					// No bot comment exists, create a new one
					const issueComment = context.issue({body: issueCommentBody});

					console.log('Creating comment:', issueCommentBody);
					await context.octokit.issues.createComment(issueComment);
				}
			} catch (error) {
				console.error('Error handling issue comments:', error);
			}
		}

        try {
			// Fetch the full repository data to ensure all necessary fields are present
			const {data: fullRepo} = await context.octokit.repos.get({
				owner: repository.owner.login,
				repo: repository.name,
			});

			// Pass the full repository object and context to sendRepo
			const repoData = await sendRepo(fullRepo, context);
			const fullData = {
				issue: issue.body || issue.title,
				repository: repoData,
			};

			if (!fullData) {
				console.error(`sendRepo returned null for ${repository.full_name}. Skipping Axios POST.`);
			} else {
				try {
					const flaskResponse = await axios.post('http://localhost:5000/report', fullData, {
						headers: {
							'Content-Type': 'application/json',
						},
					});
					if (flaskResponse.status !== 200) {
						throw new Error(`Failed to send data to Flask backend: ${flaskResponse.status} ${flaskResponse.statusText}`);
					}

					console.log('Repo info sent to Flask backend successfully from issues.opened event.');
                    sendRatings(flaskResponse.data, context);

				} catch (error) {
					console.error('Error while sending repo info from issues.opened:', error);
				}
			}
		} catch (error) {
			console.error(`Failed to fetch repository data for ${repository.full_name}:`, error);
		}
	});

};