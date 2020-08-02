export $(grep -v '^#' .env | xargs)
export $(grep -v '^#' .sec_env | xargs)