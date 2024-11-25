/**
 * Sends repository information to the Flask backend.
 *
 * @param {Object} ratings - The ratings of the top files from our bug localizer.
 * @param {Object} context - The Probot context object.
 * @returns {Object|null} - Returns the response from GitHub.
 */
export const sendRatings = async (ratings, context) => {
    const issue = context.payload.issue;
    const repository = context.payload.repository;
    const ratingsList = ratings['ranked_files'];

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
    commentBody += "\n| Rank | File Path | Score |\n";
    commentBody += "|------|-----------|-------|\n";

    let position = 1;

    for (let i = 0; i < ratingsList.length; i++) {
        const rank = ratingsList[i];
        commentBody += `| ${position++} | ${rank[0]} | ${rank[1]} |\n`;
    }

    commentBody += "\n\nPlease take the time read through each of these files. \
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
