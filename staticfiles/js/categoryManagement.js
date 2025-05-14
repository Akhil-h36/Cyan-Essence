document
  .getElementById("addCategoryForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const categoryName = document.getElementById("categoryName").value;
    const categoryDescription = document.getElementById(
      "categoryDescription"
    ).value;

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

    try {
      const response = await fetch("/admin/category", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: categoryName,
          description: categoryDescription,
        }),
      });

      const result = await response.json();
      if (response.ok) {
        await Toast.fire({
          icon: "success",
          title: result.message,
        });

        const modal = bootstrap.Modal.getInstance(
          document.getElementById("addCategoryModal")
        );
        modal.hide();

        window.location.reload();
      } else {
        Toast.fire({
          icon: "error",
          title: result.message,
        });
      }
    } catch (error) {
      Toast.fire({
        icon: "error",
        title: "Something went wrong, please try again.",
      });
    }
  });

async function handleCategoryUpdate(categoryId) {
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

  const categoryName = document.getElementById(
    `categoryName${categoryId}`
  ).value;
  const categoryDescription = document.getElementById(
    `categoryDescription${categoryId}`
  ).value;

  const data = {
    name: categoryName,
    description: categoryDescription,
  };

  try {
    const response = await fetch(`/admin/category/edit/${categoryId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      Toast.fire({
        icon: "error",
        title: "An error occurred while updating the category.",
      });
    }

    const result = await response.json(); 

    if (response.ok) {
      await Toast.fire({
        icon: "success",
        title: result.message,
      });
      const modal = bootstrap.Modal.getInstance(
        document.getElementById(`editCategoryModal${categoryId}`)
      );
      modal.hide();
      window.location.reload();
    } else {
      Toast.fire({
        icon: "error",
        title: result.message,
      });
    }
  } catch (error) {
    Toast.fire({
      icon: "error",
      title: "An error occurred while updating the category.",
    });
  }
}

async function handleCategoryDelete(categoryId) {
  // Use SweetAlert for confirmation
  const { value: confirmDelete } = await Swal.fire({
    title: 'Are you sure?',
    text: "You won't be able to revert this!",
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#3085d6',
    cancelButtonColor: '#d33',
    confirmButtonText: 'Yes, delete it!',
    cancelButtonText: 'Cancel',
  });

  // If the user clicked "Cancel", exit the function
  if (!confirmDelete) {
    return;
  }

  try {
    const response = await fetch(`/admin/category/delete/${categoryId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const result = await response.json(); // Assuming the server returns JSON

    // Handle the response
    if (result.success) {
      // Show success message with SweetAlert
      await Swal.fire(
        'Deleted!',
        'Category deleted successfully!',
        'success'
      );

      window.location.reload();
    } else {
      // Show error message with SweetAlert
      await Swal.fire(
        'Error!',
        'Error deleting category: ' + result.message,
        'error'
      );
    }
  } catch (error) {
    console.error('There was a problem with the fetch operation:', error);
    // Show error message with SweetAlert
    await Swal.fire(
      'Oops!',
      'An error occurred while deleting the category.',
      'error'
    );
  }
}

