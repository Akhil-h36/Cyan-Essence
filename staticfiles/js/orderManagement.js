function updateOrderStatus(orderId, status) {
  fetch(`/admin/orders/update-status/${orderId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status }),
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
    const response = await fetch(`/admin/orders/approve-return/${orderId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const data = await response.json();

    if (data.success) {
      Swal.fire({
        icon: 'success',
        title: 'Success',
        text: data.message,
        showConfirmButton: false,
        timer: 1500
      }).then(() => {
        window.location.reload();
      });
    } else {
      Swal.fire({
        icon: 'error',
        title: 'Error',
        text: data.message
      });
    }
  } catch (error) {
    console.error('Error:', error);
    Swal.fire({
      icon: 'error',
      title: 'Error',
      text: 'An error occurred while processing the return approval'
    });
  }
}
