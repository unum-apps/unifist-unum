# unifist-unum

Base app that sets up local ID creation and global routing

It holds the data for Unifist and Unum and is the app the others are based on. It owns and migrates the six tables everything else uses, `Sequence`, `Slug` and `Journal` (relations-unifist) and `Route`, `Scribe` and `Clash` (relations-unum), and serves them with an API and a GUI. Other apps use those tables, they don't create them.

Create a `Route` and it works.

# Requirements

- A Mac (Linux will work too but you're on your own)
- make (I think comes with xcode, git, etc)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [kubectx](https://formulae.brew.sh/formula/kubectx)
- [Tilt](https://docs.tilt.dev/install.html)

# Development

If you make changes, bump the version in `VERSION` and add to `CHANGELOG.md`.

After merging to main, update locally and type `make tag` and that'll tag with the new version.

## Actions

Make sure you also have https://github.com/gaf3/tilt-mysql up and running.

- `make up` - Fires up Tilt (run locally in Kuberentes). Hit space to open the dashboard in a browser
  - In the browser, if any micorservices (blocks) fail (turn red/yellow) click the refresh in the block
- `make down` - Removes everything locally from Kuberentes
- `make tag` - Tags this repo because you're absolutely sure this is perfect and will work
- `make untag` - Undoes the taggin you just did because you totally screwed something up

## Directories / Files

- `Makefile` - File that provides all the `make` commands
- `Tiltfile` - Deploys to the locally Kubernetes environment
- `kubernetes/` - Service Kubernetes files
  - `tilt/` - Tilt kustomization for the service to deploy locally
    - `namespace.yaml` - Namespace file
    - `kustomization.yaml` - Collates the base and microservice tilt kustomizations
- `secret/` - Directory used to create local secrets (.gitignore'd)
  - `mysql.json` - Connection informatioin for tilt-mysql
- `config/` - Directory used to create local config (.gitignore'd)

# api

Serves the six models under `/model`, with `/health` beside it. Runs the migrations before it starts.

- `cd api` - Enter this microservice
- `make build` - Build the image
- `make ddl` - Create DDL statements from the models
- `make test` - Run the tests against a throwaway MySQL
- `make lint` - Run the linter

## Directories / Files

- `bin/` - `api.py` runs the API, `migrate.py` applies the migrations, `ddl.py` generates them
- `lib/` - `service.py` builds the Flask app, `unifist_unum.py` lists the models
- `ddl/` - Generated definitions and migrations
- `test/` - Unit tests

# gui

nginx serving the Relations GUI, with the API under `/api/`.

- Local: http://localhost:5465 once `make up` is running
- API: http://localhost:15465/model
