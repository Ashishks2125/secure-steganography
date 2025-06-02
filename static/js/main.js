// Key generation
function calculatePublicKey() {
    const privateKey = parseInt(document.getElementById('keyPrivate').value);
    if (isNaN(privateKey) || privateKey < 1 || privateKey > 22) {
        alert('Please enter a valid private key (1-22)');
        return;
    }
    
    // Calculate public key: G^privateKey mod P (where G=9, P=23)
    const publicKey = Math.pow(9, privateKey) % 23;
    document.getElementById('keyPublic').value = publicKey;
}

// Encode form submission
document.getElementById('encodeForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const messageFile = document.getElementById('messageFile').files[0];
    const imageFile = document.getElementById('imageFile').files[0];
    const privateKey = document.getElementById('privateKey').value;
    const publicKey = document.getElementById('publicKey').value;
    
    if (!messageFile || !imageFile || !privateKey || !publicKey) {
        showResult('encodeResult', 'Please fill in all fields', 'danger');
        return;
    }
    
    const formData = new FormData();
    formData.append('message', messageFile);
    formData.append('image', imageFile);
    formData.append('private_key', privateKey);
    formData.append('public_key', publicKey);
    
    try {
        showResult('encodeResult', 'Encoding message, please wait...', 'info');
        
        const response = await fetch('/encode', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            // Get the filename from the Content-Disposition header
            const contentDisposition = response.headers.get('content-disposition');
            let filename = 'encoded_image.png';
            
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (filenameMatch != null && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/['"]/g, '');
                }
            }
            
            // Create a download link for the encoded image
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
            
            showResult('encodeResult', 'Message encoded successfully! The image has been downloaded.', 'success');
        } else {
            const error = await response.json();
            showResult('encodeResult', `Error: ${error.error || 'Unknown error occurred'}`, 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        showResult('encodeResult', 'An error occurred while processing your request', 'danger');
    }
});

// Decode form submission
document.getElementById('decodeForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const encodedImage = document.getElementById('encodedImage').files[0];
    const privateKey = document.getElementById('decodePrivateKey').value;
    const publicKey = document.getElementById('decodePublicKey').value;
    
    if (!encodedImage || !privateKey || !publicKey) {
        showResult('decodeResult', 'Please fill in all fields', 'danger');
        return;
    }
    
    const formData = new FormData();
    formData.append('image', encodedImage);
    formData.append('private_key', privateKey);
    formData.append('public_key', publicKey);
    
    try {
        showResult('decodeResult', 'Decoding message, please wait...', 'info');
        
        const response = await fetch('/decode', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            let message = data.message;
            
            // If the message is base64 encoded, create a download link
            if (data.is_base64) {
                try {
                    // Try to decode base64 to see if it's a valid message
                    const decoded = atob(message);
                    message = `Binary data detected. <a href="data:application/octet-stream;base64,${message}" download="decoded_message.bin" class="btn btn-sm btn-primary mt-2">Download File</a>`;
                } catch (e) {
                    // If not valid base64, show as is
                    message = `Decoded Message (Base64): <pre class="mt-2 p-2 bg-light border rounded">${escapeHtml(message)}</pre>`;
                }
            } else {
                // Regular text message
                message = `Decoded Message: <pre class="mt-2 p-2 bg-light border rounded">${escapeHtml(message)}</pre>`;
            }
            
            showResult('decodeResult', message, 'success');
        } else {
            showResult('decodeResult', `Error: ${data.error || 'Failed to decode message'}`, 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        showResult('decodeResult', 'An error occurred while processing your request', 'danger');
    }
});

// Helper function to show result messages
function showResult(elementId, message, type) {
    const resultDiv = document.getElementById(elementId);
    resultDiv.className = `alert alert-${type}`;
    resultDiv.innerHTML = message;
}

// Helper function to escape HTML
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Auto-copy public key to encode form when calculated
document.getElementById('keyPublic').addEventListener('change', function() {
    const publicKey = this.value;
    document.getElementById('publicKey').value = publicKey;
    document.getElementById('decodePublicKey').value = publicKey;
});

// Auto-copy private key to encode form when changed
document.getElementById('keyPrivate').addEventListener('change', function() {
    const privateKey = this.value;
    document.getElementById('privateKey').value = privateKey;
    document.getElementById('decodePrivateKey').value = privateKey;
});
