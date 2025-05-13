document.querySelectorAll('input[name="addressType"]').forEach(radio => {
  radio.addEventListener('change', () => {
    document.getElementById('customNameContainer').style.display = radio.id === 'custom' ? 'block' : 'none';
  });
});

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.edit-icon').forEach(icon => {
      icon.addEventListener('click', (event) => {
          event.stopPropagation(); 
          const addressId = event.target.closest('.address-card').dataset.id;
          window.location.href = `/account/addresses/edit/${addressId}`;
      });
  });
});


document.getElementById('addressForm').addEventListener('submit', function(event) {
  const checkbox = document.getElementById('defaultAddress');
  const hiddenInput = document.querySelector('input[name="isDefault"][type="hidden"]');
  
  if (checkbox.checked) {
    hiddenInput.value = true;
  } else {
    hiddenInput.value = false;
  }
});

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.delete-icon').forEach(icon => {
    icon.addEventListener('click', async (event) => {
      event.stopPropagation();
      
      const addressCard = event.target.closest('.address-card');
      const addressId = addressCard.dataset.id;

      if (confirm('Are you sure you want to delete this address?')) {
        try {
          const response = await fetch(`/account/addresses/delete/${addressId}`, {
            method: 'DELETE',
            headers: {
              'Content-Type': 'application/json',
            }
          });

          if (response.ok) {
            addressCard.remove();
            alert('Address deleted successfully.');
            window.location.reload();
          } else {
            alert('Failed to delete address.');
          }
        } catch (error) {
          console.error('Error:', error);
          alert('An error occurred while deleting the address.');
        }
      }
    });
  });
});
