# Contributing to SC_Salary_Data

I welcome all contributions, large and small, and I'm happy to help new developers get started working on public code. :heart:

If you have a feature, idea, or discover a bug, please open an [issue]( https://github.com/acrosman/sc_salary_data/issues/new) to discuss it. This will help us both to avoid spending too much time trying to implement a solution.

If you have code that addresses an issue, please make a reference to the issue in a comment on your pull request, so it is easy to see the connections. If you see a way to refactor some code, just go ahead and open a pull request when you're ready.

This project is designed for [Python 3](https://docs.python.org/3.0/) and formatted with [Flake8](https://flake8.pycqa.org/en/latest/). Please try to make sure your code changes match that standard.

Please use the standard GitHub workflow:
Here is an excellent guide for using [Git and GitHub](https://training.github.com/downloads/github-git-cheat-sheet/).

1. Fork this repository by clicking on the fork button in the upper right corner. This will create a copy of this repository to your GitHub account: "your user name"/sc_salary_data.

2. From your GitHub account, click on the green code button and then the clipboard icon. From here, you will use your command-line interface to clone the repository.
    *If you prefer, use the [GitHub Desktop app](https://desktop.github.com/). You will not use the command line with the GitHub desktop app.

Enter the following into the command prompt. In place of the <>, paste the copied URL.
```
git clone <copied url>
```

3. Create a branch for your work by changing to the directory.
```
cd sc_salary_data
```
Use the checkout -b command to create a branch to capture your work. Name it whatever you like:
```
git checkout -b <add-your-new-branch-name>
```

4. Change, edit, add or create the work to your branched repository in your text editor of choice.

5. When ready, commit your work. Use the command git status to see a list of the changes you made to your branch.
```
git status
```
If these are the changes you intended, use git add.
```
git add <file name>
```
For multiple files, use the following command:
```
git add .
```
Then commit your changes.
```
git commit -m "Add your message of the changes made."
```

6. Push to GitHub.
```
git push origin <your-branch-name>
```

7. Go back to GitHub and click the green 'Compare and Pull Request' button. Add a title and comment and click the 'create pull request' button.

Nice Job!!

I want to give contributors as much credit as reasonably possible, so I may provide you feedback on your pull request instead of just merging and fixing the issues myself. Part of collaboration is iteration, and this is the best way to move the project forward. 

Thank you for your contributions!
