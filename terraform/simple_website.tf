resource "aws_s3_bucket" "static_website" {
  bucket = var.website_domain
  #   policy = aws_s3_bucket_policy.allow_access_me_root_access.json
}

resource "aws_s3_bucket_policy" "static_website" {
  bucket = aws_s3_bucket.static_website.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource = [
          aws_s3_bucket.static_website.arn,
          "${aws_s3_bucket.static_website.arn}/*",
        ]
      },
    ]
  })
}

resource "aws_s3_bucket_acl" "static_website" {
  bucket = aws_s3_bucket.static_website.id
  acl    = "public-read"
}

resource "aws_s3_bucket_website_configuration" "static_website" {
  bucket = aws_s3_bucket.static_website.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}
