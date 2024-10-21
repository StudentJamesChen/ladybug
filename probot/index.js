/**
 * This is the main entrypoint to your Probot app
 * @param {import('probot').Probot} app
 */

import {cacheRepo} from './components/caching.js';


export default (app) => {
	app.on(["issues.opened", "issues.edited"], async (context) => {
		const issue = context.payload.issue;
		const issueBody = issue.body;

		await cacheRepo(app, context);

		let issueCommentBody = 'Thank you for opening this issue!';
		if (issueBody) {
			const imageRegex = /https?:\/\/[^\s)\]]+/g;
			const imageUrls = issueBody.match(imageRegex);

			if (imageUrls) {
				issueCommentBody += 'I found the following images in the issue description:';
				imageUrls.forEach((imageUrl) => {
					issueCommentBody += `\n\n![Image](${imageUrl})`;
				});
			} else {
				issueCommentBody = 'I did not find any images in the issue description.';
			}

			// Check if the bot already commented
			const comments = await context.octokit.issues.listComments(context.issue());
			const botComment = comments.data.find(
				comment => comment.user.type === 'Bot' && comment.body.includes('I found the following images')
			);

			if (botComment) {
				const updatedCommentBody = 'EDIT: The bug report was updated.\n\n' + issueCommentBody;

				console.log('Editing comment with ID:', botComment.id);
				try {
					await context.octokit.issues.updateComment({
						...context.issue(),
						comment_id: botComment.id,
						body: updatedCommentBody,
					});
				} catch (error) {
					console.error('Failed to update comment:', error);
				}
			} else {
				// No bot comment exists, create a new one
				const issueComment = context.issue({body: issueCommentBody});

				console.log('Creating comment:', issueCommentBody);
				try {
					await context.octokit.issues.createComment(issueComment);
				} catch (error) {
					console.error('Failed to create comment:', error);
				}
			}
		}
	});
};

