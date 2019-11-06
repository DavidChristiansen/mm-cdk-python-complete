#!/usr/bin/env bash

set -e

pool_id=$(aws cognito-idp list-user-pools --query 'UserPools[?Name==`MysfitsUserPool`].Id' --max-results 1 --output text )

if [[ -z $pool_id ]]; then
	echo Creating pool...
	aws cognito-idp create-user-pool --pool-name MysfitsUserPool --auto-verified-attributes email --output text --query 'UserPool.Id'
else
	echo Pool already exists: "$pool_id"
fi
