/**
 * Sends repository information to the Flask backend.
 *
 * @param {Object} repo - The repository object from GitHub.
 * @param {Object} context - The Probot context object.
 * @returns {Object|null} - Returns an object with repository details or null if an error occurs.
 */
export const sendRepo = async (repo, context) => {
	// Input Validation
	if (!repo || typeof repo !== 'object') {
		console.error('sendRepo Error: Invalid or missing "repo" object.');
		return null;
	}

	const {owner, name: repoName, clone_url: repoUrl, default_branch: defaultBranch} = repo;

	// Validate essential repository fields
	if (!owner || !owner.login) {
		console.error('sendRepo Error: Repository "owner" information is missing or malformed.');
		return null;
	}

	if (!repoName) {
		console.error('sendRepo Error: Repository "name" is missing.');
		return null;
	}

	if (!repoUrl) {
		console.error(`sendRepo Error: Repository URL ("clone_url") is missing for ${owner.login}/${repoName}.`);
		return null;
	}

	if (!defaultBranch) {
		console.error(`sendRepo Error: Default branch is missing for ${owner.login}/${repoName}.`);
		return null;
	}

	const ownerName = owner.login;

	// Initialize latestCommitSHA
	let latestCommitSHA;

	try {
		// Fetch the latest commit on the default branch
		const response = await context.octokit.repos.listCommits({
			owner: ownerName,
			repo: repoName,
			sha: defaultBranch,
			per_page: 1,
		});

		// Validate response structure
		if (
			!response ||
			!response.data ||
			!Array.isArray(response.data) ||
			response.data.length === 0
		) {
			console.error(`sendRepo Error: No commits found for ${ownerName}/${repoName} on branch ${defaultBranch}.`);
			return null;
		}

		latestCommitSHA = response.data[0].sha;

		if (!latestCommitSHA) {
			console.error(`sendRepo Error: Latest commit SHA is undefined for ${ownerName}/${repoName}.`);
			return null;
		}

	} catch (error) {
		// Handle specific GitHub API errors
		if (error.status === 404) {
			console.error(`sendRepo Error: Repository ${ownerName}/${repoName} not found or access denied.`);
		} else if (error.status === 403 && error.headers['x-ratelimit-remaining'] === '0') {
			console.error('sendRepo Error: GitHub API rate limit exceeded.');
		} else {
			console.error(`sendRepo Error: Failed to fetch latest commit for ${ownerName}/${repoName}:`, error.message);
		}
		return null;
	}

	// Construct the repository data object
	const repoData = {
    repo_url: repoUrl,
    owner: ownerName,
    repo_name: repoName,
    default_branch: defaultBranch,
    latest_commit_sha: latestCommitSHA,
  };

	// Additional Optional Validations
	if (!isValidRepoData(repoData)) {
		console.error(`sendRepo Error: Repository data validation failed for ${ownerName}/${repoName}.`);
		return null;
	}

	return repoData;
};

/**
 * Validates the structure and content of the repository data.
 *
 * @param {Object} data - The repository data object to validate.
 * @returns {boolean} - Returns true if valid, false otherwise.
 */
const isValidRepoData = (data) => {
	// Define required fields and their expected types
	const requiredFields = {
		repo_url: 'string',
		owner: 'string',
		repo_name: 'string',
		default_branch: 'string',
		latest_commit_sha: 'string',
	};

	for (const [field, type] of Object.entries(requiredFields)) {
		if (!(field in data)) {
			console.error(`Validation Error: Missing field "${field}" in repository data.`);
			return false;
    }
		if (typeof data[field] !== type) {
			console.error(`Validation Error: Field "${field}" should be of type ${type}, but received type ${typeof data[field]}.`);
			return false;
		}
		if (data[field].trim() === '') {
			console.error(`Validation Error: Field "${field}" cannot be empty.`);
			return false;
		}
	}

	// Updated URL Regex to allow optional .git suffix
	const urlRegex = /^(https?:\/\/)?([\w.-]+)+(:\d+)?(\/([\w/_-]+))*\.git?\/?$/;
	if (!urlRegex.test(data.repo_url)) {
		console.error(`Validation Error: Invalid repository URL format "${data.repo_url}".`);
		return false;
  }

	// SHA should be a valid Git SHA (40 hexadecimal characters)
	const shaRegex = /^[a-f0-9]{40}$/;
	if (!shaRegex.test(data.latest_commit_sha)) {
		console.error(`Validation Error: Invalid commit SHA "${data.latest_commit_sha}".`);
		return false;
	}

	return true;
};
