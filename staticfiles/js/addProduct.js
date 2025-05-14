document.addEventListener("DOMContentLoaded", () => {
  const imageInputs = document.querySelectorAll(".image-input");
  const cropButtons = document.querySelectorAll(".crop-button");
  let cropper;
  let currentPreviewId;
  let currentCropButton;

  imageInputs.forEach((input) => {
    input.addEventListener("change", (e) => {
      const file = e.target.files[0];
      const previewId = e.target.id.replace("Input", "Preview");
      const previewElement = document.getElementById(previewId);
      const cropButton = e.target
        .closest(".col-md-4")
        .querySelector(".crop-button");

      if (file) {
        const reader = new FileReader();

        reader.onload = (event) => {
          if (cropper) {
            cropper.destroy();
          }

          previewElement.src = event.target.result;
          previewElement.style.display = "block";
          cropButton.style.display = "inline-block";

          currentPreviewId = previewId;
          currentCropButton = cropButton;

          cropper = new Cropper(previewElement, {
            aspectRatio: 1,
            viewMode: 1,
          });
        };

        reader.readAsDataURL(file);
      }
    });
  });

  cropButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (cropper) {
        const croppedCanvas = cropper.getCroppedCanvas();
        const croppedImage = croppedCanvas.toDataURL();
        const previewElement = document.getElementById(currentPreviewId);

        previewElement.src = croppedImage;
        cropper.destroy();
        button.style.display = "none";
      }
    });
  });
});
