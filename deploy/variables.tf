variable "prefix" {
  default = "raad"
}

variable "project" {
  default = "recipe-app-api-devops"
}

variable "contact" {
  default = "email@gmail.com"
}

variable "db_username" {
  description = "Username for the RDS postgres instance"
}

variable "db_password" {
  description = "Password for the RDS postgres instance"
}

variable "bastion_key_name" {
  default = "recipe-app-api-devops-bastion"
}

variable "ecr_image_api" {
  description = "ECR image for API"
  default     = "191215300852.dkr.ecr.us-east-1.amazonaws.com/recipe-app-api-devops:latest"
}

variable "ecr_image_proxy" {
  description = "ECR image for proxy"
  default     = "191215300852.dkr.ecr.us-east-1.amazonaws.com/recipe-app-api-proxy:latest"
}

variable "flask_secret_key" {
  description = "Secret key for Flask app"
}