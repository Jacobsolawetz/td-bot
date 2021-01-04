# TD Trading bot

* authenticates
* reads market and account
* trades
* emails

pass your refresh token in (lasts 90 days): `docker run -e REFRESH_TOKEN=$REFRESH_TOKEN -e CLIENT_ID=$CLIENT_ID trade:v1`


`gcloud auth login`
`docker build . -t trade:v1`
`docker tag trade:v1 gcr.io/modular-truck-300500/vermillion:v1`
`docker push gcr.io/modular-truck-300500/vermillion:v1`

then launch instance in gcloud
