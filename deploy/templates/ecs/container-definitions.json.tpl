[
    {
        "name": "api",
        "image": "${app_image}",
        "essential": true,
        "memoryReservation": 256,
        "environment": [
            {"name": "SECRET_KEY", "value": "${flask_secret_key}"},
            {"name": "DB_HOST", "value": "${db_host}"},
            {"name": "DB_NAME", "value": "${db_name}"},
            {"name": "DB_USER", "value": "${db_user}"},
            {"name": "DB_PASS", "value": "${db_pass}"},
            {"name": "ALLOWED_HOSTS", "value": "${allowed_hosts}"},
            {"name": "S3_STORAGE_BUCKET_NAME", "value": "${s3_storage_bucket_name}"},
            {"name": "S3_STORAGE_REGION", "value": "${s3_storage_bucket_region}"},
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${log_group_name}",
                "awslogs-region": "${log_group_region}",
                "awslogs-stream-prefix": "api"
            }
        },
        "portMappings": [
            {
                "containerPort": 5000,
                "hostPort": 5000
            }
        ],
        "mountPoints": [
            {
                "readOnly": false,
                "containerPath": "/vol/web",
                "sourceVolume": "static"
            }
        ]
    }
]
