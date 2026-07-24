# Client1 State Backend Configuration
terraform {
  backend "s3" {
    bucket         = "deallus-tfstate-client1-REPLACE_ACCOUNT_ID"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "deallus-tfstate-lock-client1"
  }
}
