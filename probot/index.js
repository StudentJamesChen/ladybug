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

    const issueAuthor = issue.user;
    if (issueAuthor.type === 'Bot') {
        console.log(`Issue #${issue.number} opened by a bot (${issueAuthor.login}). Ignoring.`);
        return; // Exit early if the issue was opened by a bot
    }

    // Prepare data to send to Flask backend
    const issueBody = issue.body || issue.title;

    try {
        // Fetch the full repository data to ensure all necessary fields are present
        const { data: fullRepo } = await context.octokit.repos.get({
            owner: repository.owner.login,
            repo: repository.name,
        });

        // Pass the full repository object and context to sendRepo
        const repoData = await sendRepo(fullRepo, context);
        const fullData = {
            issue: issueBody,
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

                console.log('Repo info sent to Flask backend successfully from issues.opened event.', flaskResponse.data['ranked_files']);
                sendRatings(flaskResponse.data, context);

                // Extract preprocessed bug report from the Flask response
                const preprocessedBugReport = flaskResponse.data.preprocessed_bug_report;

                // Now, construct the issueCommentBody including the preprocessed bug report
                let issueCommentBody = 'Thank you for opening this issue!';

                if (preprocessedBugReport) {
                    issueCommentBody += `\n\n**Preprocessed Bug Report:**\n\n${preprocessedBugReport}`;
                } else {
                    issueCommentBody += '\n\nNo preprocessed bug report was returned.';
                }

                // Check for images in the issue body
                if (issueBody) {
                    const imageRegex = /https?:\/\/[^\s)\]]+/g;
                    const imageUrls = issueBody.match(imageRegex);

                    if (imageUrls && imageUrls.length > 0) {
                        issueCommentBody += '\n\nI found the following images in the issue description:';
                        imageUrls.forEach((imageUrl) => {
                            issueCommentBody += `\n\n![Image](${imageUrl})`;
                        });
                    } else {
                        issueCommentBody += '\n\nI did not find any images in the issue description.';
                    }
                }

                // Handle creating or updating the comment
                await handleIssueComment(context, issueCommentBody);
            } catch (error) {
                console.error('Error while sending repo info from issues.opened:', error);

                // Even if the Flask call fails, we might want to still acknowledge the issue
                let issueCommentBody = 'Thank you for opening this issue!';

                // Check for images in the issue body
                if (issueBody) {
                    const imageRegex = /https?:\/\/[^\s)\]]+/g;
                    const imageUrls = issueBody.match(imageRegex);

                    if (imageUrls && imageUrls.length > 0) {
                        issueCommentBody += '\n\nI found the following images in the issue description:';
                        imageUrls.forEach((imageUrl) => {
                            issueCommentBody += `\n\n![Image](${imageUrl})`;
                        });
                    } else {
                        issueCommentBody += '\n\nI did not find any images in the issue description.';
                    }
                }

                // Handle creating or updating the comment
                await handleIssueComment(context, issueCommentBody);
            }
        }
    } catch (error) {
        console.error(`Failed to fetch repository data for ${repository.full_name}:`, error);
    }
});

// Function to handle creating or updating the issue comment
async function handleIssueComment(context, issueCommentBody) {
    try {
        // Check if the bot already commented
        const comments = await context.octokit.issues.listComments(context.issue());
        const botComment = comments.data.find(
            (comment) => comment.user.type === 'Bot' && comment.body.includes('Thank you for opening this issue!')
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
            const issueComment = context.issue({ body: issueCommentBody });

            console.log('Creating comment:', issueCommentBody);
            await context.octokit.issues.createComment(issueComment);
        }
    } catch (error) {
        console.error('Error handling issue comments:', error);
    }
}


};