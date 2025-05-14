document.addEventListener("DOMContentLoaded", function () {
  const offerTypeSelect = document.getElementById("offerType");
  const productCategorySection = document.getElementById(
    "productCategorySection"
  );

  const productOrCategorySelect = document.getElementById("productOrCategory");

  function fetchOptions(offerType) {
    const url =
      offerType === "product"
        ? "/admin/offer/products"
        : offerType === "category"
        ? "/admin/offer/categories"
        : null;

    if (url) {
      fetch(url)
        .then((response) => response.json())
        .then((data) => {
          const options = data
            .map((item) => `<option value="${item._id}">${item.name}</option>`)
            .join("");
          productOrCategorySelect.innerHTML = `<option value="" selected>Select ${
            offerType.charAt(0).toUpperCase() + offerType.slice(1)
          }</option>${options}`;
        })
        .catch((error) => {
          console.error("Error fetching options:", error);
          productOrCategorySelect.innerHTML =
            '<option value="" selected>Error loading options</option>';
        });
    } else {
      productOrCategorySelect.innerHTML =
        '<option value="" selected>Select Product or Category</option>';
    }
  }

  offerTypeSelect.addEventListener("change", function () {
    const offerType = offerTypeSelect.value;

    // Show product/category section and update options
    if (offerType === "product" || offerType === "category") {
      productCategorySection.style.display = "block";
      fetchOptions(offerType);
    } else {
      productCategorySection.style.display = "none";
      productOrCategorySelect.innerHTML =
        '<option value="" selected>Select Product or Category</option>';
    }
  });

  document.querySelector("form").addEventListener("submit", function (event) {
    event.preventDefault();
    addOffer();
  });

  document.querySelectorAll(".edit-offer-form").forEach((form) => {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      const offerId = this.dataset.offerId; 
      updateOffer(offerId);
    });
  });
});

function addOffer() {
  let Toast = Swal.mixin({
    toast: true,
    position: "top", // Adjust position as needed
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    didOpen: (toast) => {
      toast.onmouseenter = Swal.stopTimer;
      toast.onmouseleave = Swal.resumeTimer;
    },
  });
  const offerType = document.getElementById("offerType").value;
  const productOrCategory = document.getElementById("productOrCategory").value;
  const discountType = document.getElementById("discountType").value;
  const discountValue = document.getElementById("discountValue").value;
  const maxDiscountAmount =
    document.getElementById("maxDiscountAmount").value || null;
  const minCartValue = document.getElementById("minCartValue").value || null;
  const validFrom = document.getElementById("validFrom").value;
  const validUntil = document.getElementById("validUntil").value;


  const offerData = {
    type: offerType,
    product: offerType === "product" ? productOrCategory : undefined,
    category: offerType === "category" ? productOrCategory : undefined,
    discountType,
    discountValue,
    maxDiscountAmount,
    minCartValue,
    validFrom,
    validUntil,
  };

  fetch("/admin/offer", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(offerData),
  })
    .then((response) => response.json())
    .then(async (data) => {
      if (data.success) {
        await Toast.fire({
          icon: "success",
          title: `${data.message}`,
        });
        const modal = bootstrap.Modal.getInstance(
          document.getElementById("addOfferModal")
        );
        modal.hide();
        window.location.reload();
      } else {
        Toast.fire({
          icon: "error",
          title: `${data.message}`,
        });
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      Toast.fire({
        icon: "error",
        title: "An error occurred while adding the offer.",
      });
    });
}

function updateOffer(offerId) {
  let Toast = Swal.mixin({
    toast: true,
    position: "top", // Adjust position as needed
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    didOpen: (toast) => {
      toast.onmouseenter = Swal.stopTimer;
      toast.onmouseleave = Swal.resumeTimer;
    },
  });
  const offerType = document.getElementById(`offerType${offerId}`).value;
  const discountType = document.getElementById(`discountType${offerId}`).value;
  const discountValue = document.getElementById(`discountValue${offerId}`).value;
  const maxDiscountAmount =
    document.getElementById(`maxDiscount${offerId}`).value || null;
  const validFrom = document.getElementById(`validFrom${offerId}`).value;
  const validUntil = document.getElementById(`validUntil${offerId}`).value;
  const minCartValue = document.getElementById(`minCartValue${offerId}`).value || null;

  const offerData = {
    type: offerType,
    discountType,
    discountValue,
    maxDiscountAmount,
    validFrom,
    validUntil,
    minCartValue,
  };

  fetch(`/admin/offer/update/${offerId}`, {
    method: "POST", 
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(offerData),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        Toast.fire({
          icon: "success",
          title: `${data.message}`,
        });
        const modal = bootstrap.Modal.getInstance(
          document.getElementById(`editOfferModal${offerId}`)
        );
        modal.hide();
        window.location.reload();
      } else {
        Toast.fire({
          icon: "error",
          title: `${data.message}`,
        });
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      Toast.fire({
        icon: "error",
        title: "An error occurred while adding the offer.",
      });
    });
}

function deleteOffer(offerId) {
  let Toast = Swal.mixin({
    toast: true,
    position: "top", // Adjust position as needed
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    didOpen: (toast) => {
      toast.onmouseenter = Swal.stopTimer;
      toast.onmouseleave = Swal.resumeTimer;
    },
  });
  Swal.fire({
    title: "Are you sure?",
    text: "You won't be able to revert this!",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#3085d6",
    cancelButtonColor: "#d33",
    confirmButtonText: "Yes, delete it!",
  }).then((result) => {
    if (result.isConfirmed) {
      fetch(`/admin/offer/delete/${offerId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            Toast.fire({
              icon: "success",
              title: "Offer deleted successfully!",
            });

            // Remove the row from the table (simple way)
            const offerRow = document.querySelector(`tr[data-offer-id="${offerId}"]`);
            if (offerRow) {
              offerRow.remove();
            }
          } else {
            Toast.fire({
              icon: "error",
              title: "Error: " + data.message,
            });
          }
        })
    }
  }).catch((error) => {
    console.error("Error:", error);
    Toast.fire({
      icon: "error",
      title: "An error occurred while deleting the offer.",
    });
  });
}

async function toggleOfferStatus(offerId) {
  try {
    const response = await fetch(`/admin/offer/toggle/${offerId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      }
    });

    const result = await response.json();

    if (result.success) {
      // Update the UI with the new status
      const badge = document.getElementById(`statusDisplay${offerId}`);
      const newStatus = result.offer.status; // Get the updated value from the response

      badge.classList.remove(newStatus === 'active' ? 'bg-danger' : 'bg-success');
      badge.classList.add(newStatus === 'active' ? 'bg-success' : 'bg-danger');
      badge.textContent = newStatus;
    } else {
      console.error("Error updating status:", result.message);
    }
  } catch (error) {
    console.error("Error toggling offer status:", error);
  }
}
