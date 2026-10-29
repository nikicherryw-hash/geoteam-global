"use strict";
/* Deploy only after verified GeoTeam Firebase ownership and explicit release approval. */
const {onRequest}=require("firebase-functions/v2/https");
const {sourceApi}=require("./directory-api");
exports.sourcing=onRequest({
 region:"europe-west1",
 memory:"256MiB",
 timeoutSeconds:10,
 maxInstances:4,
 minInstances:0,
 cors:false
},sourceApi);
