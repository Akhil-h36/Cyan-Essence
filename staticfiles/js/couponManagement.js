document.querySelector("#addCouponform").addEventListener("submit", async function (event) {
  event.preventDefault();
  let Toast = Swal.mixin({
    toast: true,
    position: "top",
    showConfirmButton: false,
    timer: 2500,
    timerProgressBar: true,
    didOpen: (toast) => {
      toast.onmouseenter = Swal.stopTimer;
      toast.onmouseleave = Swal.resumeTimer;
    },
  });

  const couponCode = document.getElementById("couponCode").value;
  const discountType = document.getElementById("discountType").value;
  const discountValue = document.getElementById("discountValue").value;
  const maxDiscountValue = document.getElementById("maxDiscountValue").value;
  const minCartValue = document.getElementById("minCartValue").value;
  const validFrom = document.getElementById("validFrom").value;
  const validUntil = document.getElementById("validUntil").value;
  const usageLimit = document.getElementById("usageLimit").value;
  const isActive = document.getElementById("isActive").value === "true";

  if (
    !couponCode ||
    !discountType ||
    !discountValue ||
    !validFrom ||
    !validUntil
  ) {
    await Toast.fire({
      icon: "warning",
      title: "Please fill in all required fields",
    });
    return;
  }

  const couponData = {
    code: couponCode,
    discountType,
    discountValue: parseFloat(discountValue),
    maxDiscountValue: maxDiscountValue ? parseFloat(maxDiscountValue) : 0,
    minCartValue: minCartValue ? parseFloat(minCartValue) : 0,
    validFrom, 
    validUntil, 
    usageLimit: parseInt(usageLimit, 10),
    isActive,
};

  try {
    const response = await fetch("/admin/coupon/add", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(couponData),
    });

    const result = await response.json();

    if (response.ok) {
      await Toast.fire({
        icon: "success",
        title: "Coupon added successfully!",
      });
      document.getElementById("addCouponform").reset();

      // Hide the modal
      const addCouponModal = new bootstrap.Modal(
        document.getElementById("addCouponModal")
      );
      addCouponModal.hide();
      window.location.reload();
    } else {
      Toast.fire({
        icon: "error",
        title: `Error adding coupon: ${result.message || "Unknown error"}`,
      });
    }
  } catch (error) {
    console.error("Error:", error);
    Toast.fire({
      icon: "error",
      title: "An error occurred while adding the coupon.",
    });
  }
});

document.querySelectorAll(".edit-coupon-form").forEach(form => {
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    const couponId = this.getAttribute("data-coupon-id");
    updateCoupon(couponId);
  });
});


async function updateCoupon(couponId) {
  let Toast = Swal.mixin({
    toast: true,
    position: "top",
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    didOpen: (toast) => {
      toast.onmouseenter = Swal.stopTimer;
      toast.onmouseleave = Swal.resumeTimer;
    },
  });

  const couponCode = document.getElementById(`couponCode${couponId}`).value;
  const discountType = document.getElementById(`discountType${couponId}`).value;
  const discountValue = document.getElementById(`discountValue${couponId}`).value;
  const maxDiscountValue =
    document.getElementById(`maxDiscountValue${couponId}`).value || null;
  const minCartValue = document.getElementById(`minCartValue${couponId}`).value || null;
  const validFrom = document.getElementById(`validFrom${couponId}`).value;
  const validUntil = document.getElementById(`validUntil${couponId}`).value;
  const usageLimit = document.getElementById(`usageLimit${couponId}`).value || null;
  const isActive = document.getElementById(`isActive${couponId}`).checked; // Corrected to boolean

  if (
    !couponCode ||
    !discountType ||
    !discountValue ||
    !validFrom ||
    !validUntil
  ) {
    await Toast.fire({
      icon: "warning",
      title: "Please fill in all required fields",
    });
    return;
  }

  const couponData = {
    code: couponCode,
    discountType,
    discountValue: parseFloat(discountValue),
    maxDiscountValue: maxDiscountValue ? parseFloat(maxDiscountValue) : undefined,
    minCartValue: minCartValue ? parseFloat(minCartValue) : 0,
    validFrom,
    validUntil,
    usageLimit: parseInt(usageLimit, 10),
    isActive,
  };

  try {
    const response = await fetch(`/admin/coupon/update/${couponId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(couponData),
    });

    const result = await response.json();

    if (response.ok) {
      const updatedCoupon = result.coupon;
      document.getElementById(`couponCodeDisplay${couponId}`).textContent = updatedCoupon.code;

      document.getElementById(`discountTypeDisplay${couponId}`).textContent =
      updatedCoupon.discountType === 'percentage' ? `${updatedCoupon.discountValue}%` : `₹${updatedCoupon.discountValue}`;

      document.getElementById(`maxDiscountValueDisplay${couponId}`).textContent =
        updatedCoupon.maxDiscountValue ? `₹${updatedCoupon.maxDiscountValue}` : '-';
      document.getElementById(`minCartValueDisplay${couponId}`).textContent =
        updatedCoupon.minCartValue ? `₹${updatedCoupon.minCartValue}` : '-';
      document.getElementById(`usageLimitDisplay${couponId}`).textContent =
        updatedCoupon.usageLimit || 'Unlimited';
      document.getElementById(`validFromDisplay${couponId}`).textContent = new Date(updatedCoupon.validFrom).toLocaleDateString();
      document.getElementById(`validUntilDisplay${couponId}`).textContent = new Date(updatedCoupon.validUntil).toLocaleDateString();
      document.getElementById(`isActiveDisplay${couponId}`).innerHTML =
        `<span class="badge w-100  ${updatedCoupon.isActive ? 'bg-success' : 'bg-danger'}">${updatedCoupon.isActive ? 'Active' : 'Inactive'}</span>`;

      Toast.fire({
        icon: "success",
        title: result.message,
      });
      const modal = bootstrap.Modal.getInstance(
        document.getElementById(`editCouponModal${couponId}`)
      );
      modal.hide();
    } else {
      Toast.fire({
        icon: "error",
        title: `Error updating coupon: ${result.message || "Unknown error"}`,
      });
    }
  } catch (error) {
    console.error("Error:", error);
    Toast.fire({
      icon: "error",
      title: `An error occurred while updating the coupon. ${error}`,
    });
  }
}

async function deleteCoupon(couponId) {
  let Toast = Swal.mixin({
    toast: true,
    position: "top",
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    didOpen: (toast) => {
      toast.onmouseenter = Swal.stopTimer;
      toast.onmouseleave = Swal.resumeTimer;
    },
  });

  const confirmDelete = await Swal.fire({
    title: 'Are you sure?',
    text: "This action cannot be undone!",
    icon: 'warning',
    showCancelButton: true,
    confirmButtonText: 'Yes, delete it!',
    cancelButtonText: 'Cancel',
  });

  if (!confirmDelete.isConfirmed) {
    return; // Exit if the user cancels the deletion
  }

  try {
    const response = await fetch(`/admin/coupon/delete/${couponId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const result = await response.json();

    if (response.ok) {
      // Remove the coupon's row from the table
      const row = document.querySelector(`tr[data-coupon-id="${couponId}"]`);
      if (row) row.remove();

      Toast.fire({
        icon: "success",
        title: "Coupon deleted successfully!",
      });
    } else {
      Toast.fire({
        icon: "error",
        title: `Error deleting coupon: ${result.message || "Unknown error"}`,
      });
    }
  } catch (error) {
    console.error("Error:", error);
    Toast.fire({
      icon: "error",
      title: "An error occurred while deleting the coupon.",
    });
  }
}

async function toggleCouponStatus(couponId) {
  try {
    const response = await fetch(`/admin/coupon/toggle-status/${couponId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      }
    });

    const result = await response.json();

    if (result.success) {
      // Update the UI with the new status
      const badge = document.getElementById(`isActiveDisplay${couponId}`);
      const newStatus = result.coupon.isActive; // Get the updated value from the response

      badge.classList.remove(newStatus ? 'bg-danger' : 'bg-success');
      badge.classList.add(newStatus ? 'bg-success' : 'bg-danger');
      badge.textContent = newStatus ? 'Active' : 'Inactive';
    } else {
      console.error("Error updating status:", result.message);
    }
  } catch (error) {
    console.error("Error toggling coupon status:", error);
  }
}

