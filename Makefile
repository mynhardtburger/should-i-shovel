ssh-app:
	terraform -chdir=./terraform output -raw private_key > ~/.ssh/shouldishovel.pem && chmod 600 ~/.ssh/shouldishovel.pem && ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i ~/.ssh/shouldishovel.pem ubuntu@$$(terraform -chdir=./terraform output -raw ec2_public_dns) && rm ~/.ssh/shouldishovel.pem
