resource "aws_s3_bucket" "app_public_files" {
  bucket        = "${local.prefix}-files"
  acl           = "public-read"
  force_destroy = true # set to false for production
}