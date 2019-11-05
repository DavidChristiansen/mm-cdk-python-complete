#!/usr/bin/env bash

set -e

client_id=$( aws cognito-idp list-user-pool-clients --user-pool-id "$USER_POOL" --query 'UserPoolClients[].ClientId' --output text )

if [[ -z $client_id ]]; then
	echo Creating user pool client...
	aws cognito-idp create-user-pool-client --user-pool-id "$USER_POOL" --client-name MysfitsUserPoolClient
else
	echo Client already exists: "$client_id"
fi
