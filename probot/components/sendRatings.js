/**
 * Sends repository information to the Flask backend.
 *
 * @param {Object} ratings - The ratings of the top files from our bug localizer.
 * @param {Object} context - The Probot context object.
 * @returns {Object|null} - Returns the response from GitHub.
 */
export const sendRatings = async(ratings, context) => {
    const issue = context.payload.issue;
    const repository = context.payload.repository;
    const ratingsList = ratings.files;

    try {
        let commentBody = "Hello! LadyBug was able to find and rank files that may contain the bug associated with this issue:\n";
        let position = 1;

        for (let i = 0; i < ratingsList.length; i++)
        {
            commentBody += `\n**${position++}. ${ratingsList[i]}**`;
        }
        
        commentBody += "\n\nPlease take the time read through each of these files. \
        \nIf you have any problems with this response, or if you think LadyBug did a bad job, please take the time to create an issue here: [ladybug issues](https://github.com/LadyBugML/ladybug/issues/new)";

        console.log(`Sending the ratings to issue #${issue.number} for repository ${repository.full_name}.`);

        const issueComment = context.issue({body: commentBody});
        await context.octokit.issues.createComment(issueComment);
    } catch (error) {
        console.error('Error creating rankings comment:', error);
    }
}