output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "nat_instance_ids" {
  description = "List of NAT instance IDs"
  value       = aws_instance.nat[*].id
}

output "nat_ips" {
  description = "List of NAT instance EIPs"
  value       = aws_eip.nat[*].public_ip
}

output "security_groups" {
  description = "Map of security group IDs"
  value = {
    alb      = aws_security_group.alb.id
    eks      = aws_security_group.eks_nodes.id
    rds      = aws_security_group.rds.id
    redis    = aws_security_group.redis.id
    efs      = aws_security_group.efs.id
  }
}

output "internet_gateway_id" {
  description = "Internet Gateway ID"
  value       = aws_internet_gateway.main.id
}
