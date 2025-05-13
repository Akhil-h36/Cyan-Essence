document.addEventListener('DOMContentLoaded', function() {
    // Add Coupon Form Submission
    const addCouponForm = document.getElementById('addCouponform');
    if (addCouponForm) {
      addCouponForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Convert coupon code to uppercase
        const couponCodeInput = document.getElementById('couponCode');
        couponCodeInput.value = couponCodeInput.value.toUpperCase();
        
        // Get form data
        const formData = {
          action: 'add',
          couponCode: document.getElementById('couponCode').value,
          description: document.getElementById('description').value,
          discountType: document.getElementById('discountType').value,
          discountValue: document.getElementById('discountValue').value,
          maxDiscountValue: document.getElementById('maxDiscountValue').value || null,
          minCartValue: document.getElementById('minCartValue').value || null,
          validFrom: document.getElementById('validFrom').value,
          validUntil: document.getElementById('validUntil').value,
          usageLimit: document.getElementById('usageLimit').value || null,
          isActive: document.getElementById('isActive').value
        };
        
        // Send AJAX request to the correct URL
        fetch('/adminapp/coupons/', {  // Changed from /admin/coupons to /adminapp/coupons/
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify(formData)
        })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          if (data.status === 'success') {
            // Show success message
            alert(data.message);
            // Reload the page to show the new coupon
            window.location.reload();
          } else {
            // Show error message
            alert('Error: ' + data.message);
          }
        })
        .catch(error => {
          console.error('Error:', error);
          alert('An error occurred while adding the coupon.');
        });
      });
    }
    
    // Edit Coupon Form Submission
    const editCouponForms = document.querySelectorAll('.edit-coupon-form');
    editCouponForms.forEach(form => {
      form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const couponId = this.getAttribute('data-coupon-id');
        
        // Convert coupon code to uppercase
        const couponCodeInput = document.getElementById(`couponCode${couponId}`);
        couponCodeInput.value = couponCodeInput.value.toUpperCase();
        
        // Get form data
        const formData = {
          action: 'update',
          couponId: couponId,
          couponCode: document.getElementById(`couponCode${couponId}`).value,
          description: document.getElementById(`description${couponId}`).value,
          discountType: document.getElementById(`discountType${couponId}`).value,
          discountValue: document.getElementById(`discountValue${couponId}`).value,
          maxDiscountValue: document.getElementById(`maxDiscountValue${couponId}`).value || null,
          minCartValue: document.getElementById(`minCartValue${couponId}`).value || null,
          validFrom: document.getElementById(`validFrom${couponId}`).value,
          validUntil: document.getElementById(`validUntil${couponId}`).value,
          usageLimit: document.getElementById(`usageLimit${couponId}`).value || null,
          isActive: document.getElementById(`isActive${couponId}`).checked
        };
        
        // Send AJAX request to the correct URL
        fetch('/adminapp/coupons/', {  // Changed from /admin/coupons to /adminapp/coupons/
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify(formData)
        })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          if (data.status === 'success') {
            // Show success message
            alert(data.message);
            
            // Update the display in the table
            document.getElementById(`couponCodeDisplay${couponId}`).textContent = formData.couponCode;
            
            // Update discount type display
            const discountTypeDisplay = document.getElementById(`discountTypeDisplay${couponId}`);
            if (formData.discountType === 'percentage') {
              discountTypeDisplay.textContent = formData.discountValue + '%';
            } else {
              discountTypeDisplay.textContent = '₹' + formData.discountValue;
            }
            
            // Update other fields
            document.getElementById(`maxDiscountValueDisplay${couponId}`).textContent = 
              formData.maxDiscountValue ? '₹' + formData.maxDiscountValue : '-';
            document.getElementById(`minCartValueDisplay${couponId}`).textContent = 
              formData.minCartValue ? '₹' + formData.minCartValue : '-';
            document.getElementById(`usageLimitDisplay${couponId}`).textContent = 
              formData.usageLimit ? formData.usageLimit : 'Unlimited';
            document.getElementById(`validFromDisplay${couponId}`).textContent = formData.validFrom;
            document.getElementById(`validUntilDisplay${couponId}`).textContent = formData.validUntil;
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById(`editCouponModal${couponId}`));
            modal.hide();
          } else {
            // Show error message
            alert('Error: ' + data.message);
          }
        })
        .catch(error => {
          console.error('Error:', error);
          alert('An error occurred while updating the coupon.');
        });
      });
    });
    
    // Function to get CSRF token from cookies
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
  });
  
  // Delete coupon function
  function deleteCoupon(couponId) {
    if (confirm('Are you sure you want to delete this coupon?')) {
      fetch('/adminapp/coupons/', {  // Changed from /admin/coupons to /adminapp/coupons/
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          action: 'delete',
          couponId: couponId
        })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.status === 'success') {
          // Show success message
          alert(data.message);
          // Remove the row from the table
          const row = document.querySelector(`tr[data-coupon-id="${couponId}"]`);
          if (row) {
            row.remove();
          }
          // If no coupons left, reload to show the "No coupons found" message
          const tbody = document.querySelector('tbody');
          if (tbody && tbody.children.length === 0) {
            window.location.reload();
          }
        } else {
          // Show error message
          alert('Error: ' + data.message);
        }
      })
      .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while deleting the coupon.');
      });
    }
  }
  
  // Toggle coupon status function
  function toggleCouponStatus(couponId) {
    fetch('/adminapp/coupons/', {  // Changed from /admin/coupons to /adminapp/coupons/
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({
        action: 'toggle_status',
        couponId: couponId
      })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.status === 'success') {
        // Update the status badge
        const statusBadge = document.getElementById(`isActiveDisplay${couponId}`);
        if (statusBadge) {
          if (data.is_active) {
            statusBadge.textContent = 'Active';
            statusBadge.classList.remove('bg-danger');
            statusBadge.classList.add('bg-success');
          } else {
            statusBadge.textContent = 'Inactive';
            statusBadge.classList.remove('bg-success');
            statusBadge.classList.add('bg-danger');
          }
        }
      } else {
        // Show error message
        alert('Error: ' + data.message);
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('An error occurred while updating the coupon status.');
    });
  }
  
  // Helper function for CSRF token
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