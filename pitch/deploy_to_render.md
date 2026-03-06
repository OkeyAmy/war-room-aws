# WAR ROOM Pitch Deck — Render Deployment Guide

To deploy this static pitch deck on [Render](https://render.com), which is perfect for hosting fast, free static HTML content, follow these simple steps.

## Step 1: Push the Pitch Folder to GitHub

Render connects directly to your GitHub repository. Ensure your `pitch` directory (containing `index.html`) is pushed to a GitHub repository.

If you want to deploy *only* the pitch deck and not the entire backend, it's best to ensure it's in its own dedicated folder or its own repository. Assuming you want to deploy the existing repo:

## Step 2: Create a New Static Site on Render

1. Log in to [dashboard.render.com](https://dashboard.render.com/)
2. Click the **"New"** button in the top right, then select **"Static Site"**.
3. Connect your GitHub account and select the repository where this project lives.

## Step 3: Configure the Deployment Setting

Fill out the configuration page with these exact settings:

* **Name:** `war-room-pitch` (or whatever you prefer)
* **Branch:** `main` (or the branch you pushed to)
* **Publish Directory:** `./pitch`
  > [!IMPORTANT]
  > This is the most crucial part! Because the repository has a backend and project folders, you must explicitly tell Render that the only folder it needs to serve to the internet is `./pitch`.
* **Build Command:** *(Leave this completely blank. It is pure HTML/CSS, so no build step is required.)*

## Step 4: Deploy

Click the **"Create Static Site"** button at the bottom.
Render will instantly pull your code and serve the `index.html` file located in the `pitch` directory onto a global CDN.
Within seconds, you will receive a live URL (e.g., `https://war-room-pitch.onrender.com`) that you can share or use on the presenter's screen during the hackathon!
