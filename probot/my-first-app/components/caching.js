import AdmZip from 'adm-zip';
import path from "path";
import fs from "fs";
import fetch from "node-fetch";
import { FormData } from 'node-fetch';

export const cacheRepo = async (app, context) => {
	const repo = context.payload.repository;
	const repoName = repo.name;
	const hostName = repo.owner.login;

	console.log('Caching repo:', repoName);
	console.log('Caching repo:', hostName);

	try {
		const response = await context.octokit.request('GET /repos/{owner}/{repo}/zipball/{ref}', {
			owner: hostName,
			repo: repoName,
			ref: 'main'
		});

		const zipUrl = response.url;
		// Remember to fetch the zip file. This is an async operation.
		const zipResponse = await fetch(zipUrl);

		// The zip file is a binary file, so we need to convert it to a buffer then save it to disk.
		const arrayBuffer = await zipResponse.arrayBuffer();
		const buffer = Buffer.from(arrayBuffer);

		// Define the directory to cache. Reminder to gitignore this directory so we dont end up with infinite files :)
		const cacheDir = path.resolve(`./cached_repos/${repoName}`);
		fs.mkdirSync(cacheDir, {recursive: true});

		// Storing the zip file
		const zipPath = path.resolve(cacheDir, `${repoName}.zip`);
		fs.writeFileSync(zipPath, buffer);

		console.log(`Repo ${repoName} cached successfully at ${zipPath}`);

		// Extract zip file
		const zip = new AdmZip(zipPath);
		zip.extractAllTo(cacheDir, true);
        
		console.log(`Repo ${repoName} extracted successfully to ${cacheDir}`);

        // TODO: Send zip to Flask backend
        const flask_response = await fetch(`http://localhost:5000/preprocess`, {
            method: "POST",
            body: JSON.stringify({"path" : cacheDir}),
        });

	} catch (error) {
		console.error('Error while caching repo:', error);
	}
}
