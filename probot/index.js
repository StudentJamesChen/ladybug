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
				const initIssue = await context.octokit.issues.create({
					owner: ownerName,
					repo: repoName,
					title: 'Welcome to LadyBug! 🐞',
					body: getInitializationComment(repoName),
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

                    await context.octokit.issues.createComment({
                        owner: ownerName,
                        repo: repoName,
                        issue_number: initIssue.data.number,
                        body: getCompletionComment(repoName)
                    })
				} catch (error) {
					console.error('Error while sending repo info:', error);
				}
			}
		} catch (error) {
			console.error('Failed to process repositories:', error);
		}
	});


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

      if (!repoData) {
        console.error(`sendRepo returned null for ${repository.full_name}. Skipping Axios POST.`);
        // Reply to the issue with an error message
        await replyWithError(context, issue.number, "An error occurred while processing the repository data.");
        return; // Return early if repoData is null
      }

      const fullData = {
        issue: issueBody,
        repository: repoData,
      };

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

        // Await sendRatings to handle potential errors
        await sendRatings(flaskResponse.data, context);

      } catch (error) {
        console.error('Error while sending repo info from issues.opened:', error.message);
        // Reply to the issue with an error message
        await replyWithError(context, issue.number, "An error occurred while communicating with the analysis backend.");
      }

    } catch (error) {
      console.error(`Failed to fetch repository data for ${repository.full_name}:`, error.message);
      // Reply to the issue with an error message
      await replyWithError(context, issue.number, "An error occurred while fetching repository data.");
    }
  });

 /**
 * Replies to the issue with an error message.
 *
 * @param {Object} context - The Probot context object.
 * @param {number} issueNumber - The issue number to reply to.
 * @param {string} errorMessage - The error message to include in the comment.
 */
const replyWithError = async (context, issueNumber, errorMessage) => {
  const commentBody = `Hello! Unfortunately, ${errorMessage} Please try again later or contact support if the issue persists.`;

  const issueComment = context.issue({ body: commentBody, issue_number: issueNumber });

  try {
    await context.octokit.issues.createComment(issueComment);
    console.log(`Posted error message to issue #${issueNumber}.`);
  } catch (error) {
    console.error('Failed to post error message to issue:', error.message);
  }
};

function getInitializationComment(repoName) {
    return `
# Hang Tight, We're Getting Ready! ⏳

Hello, ${repoName}!

I've been invited to your repository, and I'm thrilled to get started! 🎉 I'm currently working behind the scenes to process your codebase and prepare everything I need to assist you with bug localization. 

Initialization might take a few minutes, so hang tight while I set things up. Here's what I'm doing:
- 🪄 Preprocessing all source code files.
- 🔍 Generating embeddings for smarter bug tracking.
- 🔄 Setting up my internal database for your repo.

I'll let you know as soon as the setup is complete with a follow-up comment below. Thank you for your patience!
`;
}

function getCompletionComment(repoName) {
    return `
# All Set! 🎉

Good news, ${repoName}! 🥳 

The initialization process is now complete, and I'm ready to assist you with your bug localization needs. Here's what I've done:
- ✅ Successfully preprocessed all source code files.
- ✅ Generated embeddings for better bug analysis.
- ✅ Fully integrated with your repository.

To get assistance localizing bugs, create a new issue and I will automatically take a look.

I'm here to help you save time and debug smarter. Let the journey to cleaner code begin! 🚀

---

Happy debugging,  
LadyBug 🐞
`;
}

};