variable "prefix" {
  default = "alpine"
}

variable "project" {
  default = "alpineapp"
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
  default = "nghia-alpine-bastion"
}

variable "ecr_image_api" {
  description = "ECR image for API"
  default     = "291857152056.dkr.ecr.ap-southeast-1.amazonaws.com/alpineapp-api:latest"
}

variable "flask_secret_key" {
  description = "Secret key for Flask app"
}