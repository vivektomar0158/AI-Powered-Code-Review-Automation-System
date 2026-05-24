import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    """
    Verifies that the webhook payload matches the signature sent by GitHub.
    Uses HMAC with SHA256.
    """
    if not signature_header or not secret:
        return False
        
    # GitHub signature header format: "sha256=..."
    if not signature_header.startswith("sha256="):
        return False
        
    received_signature = signature_header.split("sha256=")[-1]
    
    # Calculate expected signature
    mac = hmac.new(
        secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    )
    expected_signature = mac.hexdigest()
    
    # Use hmac.compare_digest to prevent timing attacks
    return hmac.compare_digest(received_signature, expected_signature)
