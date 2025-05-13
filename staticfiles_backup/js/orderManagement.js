function updateOrderStatus(orderId, status) {
  fetch(`adminapp/admin/update_order_status/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie('csrftoken')
    },
    body: JSON.stringify({ order_id: orderId, status: status }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert("Order status updated successfully");
      } else {
        alert("Error updating order status");
      }
    });
}

async function approveReturn(orderId) {
  try {
    // Get CSRF token
    const csrftoken = getCookie('csrftoken');
    
    // Create FormData object
    const formData = new FormData();
    formData.append('order_id', orderId);
    
    // Make the request
    const response = await fetch('/adminapp/admin/approve_return_request/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken
      },
      body: formData
    });

    const data = await response.json();

    if (data.success) {
      alert('Success: ' + data.message);
      window.location.reload();
    } else {
      alert('Error: ' + (data.message || 'Error processing return request'));
    }
  } catch (error) {
    console.error('Error:', error);
    alert('An error occurred while processing the return approval');
  }
}

// Helper function to get CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}