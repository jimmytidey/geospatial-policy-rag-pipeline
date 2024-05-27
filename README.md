# Deploying

heroku create your-app-name
heroku buildpacks:set heroku/python
heroku buildpacks:add --index 1 heroku/nodejs
git push heroku master
