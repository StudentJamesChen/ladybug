// sendRatings.js

import axios from 'axios';
/**
 * Sends repository information to the Flask backend and handles commenting on the issue.
 *
 * @param {Object|null} ratingsData - The response data from the Flask backend.
 * @param {Object} context - The Probot context object.
 * @param {string} baseComment - The base comment message to start with.
 * @param {string} issueBody - The body of the GitHub issue.
 */
export const sendRatingsAndComment = async (ratingsData, context, baseComment, issueBody) => {
    const issue = context.payload.issue;
    const repository = context.payload.repository;

    let issueCommentBody = baseComment;

    // Handle Flask response
    if (ratingsData) {
        // Handle ratings
        await handleRatings(ratingsData, context);

        // Extract preprocessed bug report from the Flask response
        const preprocessedBugReport = ratingsData.preprocessed_bug_report;

        // Append preprocessed bug report if available
        if (preprocessedBugReport) {
            issueCommentBody += `\n\n**Preprocessed Bug Report:**\n\n${preprocessedBugReport}`;
        } else {
            issueCommentBody += '\n\nNo preprocessed bug report was returned.';
        }
    } else {
        // If ratingsData is null, an error occurred during processing
        issueCommentBody += '\n\nWe encountered an error while processing your issue. Please try again later.';
    }

    // Append image information
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
};

/**
 * Handles the ratings data by commenting on the issue.
 *
 * @param {Object} ratingsData - The response data from the Flask backend.
 * @param {Object} context - The Probot context object.
 */
const handleRatings = async (ratingsData, context) => {
    const issue = context.payload.issue;
    const repository = context.payload.repository;
    const ratingsList = ratingsData.files;

    if (!ratingsList || ratingsList.length < 1) {
        console.error(`Ratings list is empty; sending a msg to issue #${issue.number} on ${repository.full_name}.`);

        const commentBody = "Hello! LadyBug was unable to find any files that might have contained the bug mentioned in this issue.\
            \n\nIf you think this is a problem or bug, please take the time to create a bug report here: [ladybug issues](https://github.com/LadyBugML/ladybug/issues/new)";
        const issueComment = context.issue({ body: commentBody });
        try {
            await context.octokit.issues.createComment(issueComment);
            console.log("Ratings comment was successful.");
        } catch (error) {
            console.error("Could not create issue message: ", error);
        }
        return;
    }

    let commentBody = "Hello! LadyBug was able to find and rank files that may contain the bug mentioned in this issue. \
    \n## File ranking in order of most likely to contain the bug to least likely:\n";
    let position = 1;

    for (let i = 0; i < ratingsList.length; i++) {
        commentBody += `\n**${position++}. ${ratingsList[i]}**`;
    }

    commentBody += "\n\nPlease take the time to read through each of these files. \
    \nIf you have any problems with this response, or if you think an error occurred, please take the time to create an issue here: [ladybug issues](https://github.com/LadyBugML/ladybug/issues/new). \
    \nHappy coding!";

    console.log(`Sending the ratings to issue #${issue.number} for repository ${repository.full_name}.`);

    const issueComment = context.issue({ body: commentBody });

    try {
        await context.octokit.issues.createComment(issueComment);
        console.log("Ratings comment was successful.");
    } catch (error) {
        console.error('Could not create issue message: ', error);
    }
};

/**
 * Function to handle creating or updating the issue comment
 *
 * @param {Object} context - The Probot context object.
 * @param {string} issueCommentBody - The body of the comment to create or update.
 */
const handleIssueComment = async (context, issueCommentBody) => {
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
};