document.addEventListener("DOMContentLoaded", function () {
    const inputField = document.getElementById("chat-input");
    const promptDisplay = document.getElementById("prompt-display");
    const imageContainer = document.getElementById("generated-images-container");
    const saveButton = document.getElementById("save-button");

    const colorPicker = document.getElementById("color-picker");
    const colorPickerLabel = document.getElementById("color-picker-label");

        // Map of readable names for colormaps
    const colormapNames = {
            "gray_r": "Black (Default)",
            "gray": "Inverse Background",
            "Blues": "Blue",
            "Greens": "Green",
            "Reds": "Red",
            "Purples": "Purple",
            "YlGnBu": "Yellow-Blue",
            "twilight": "Twilight",
            "inferno": "Inferno",
            "magma": "Magma",
            "plasma": "Plasma",
            "viridis": "Viridis",
            "cividis": "Cividis",
            "Spectral": "Spectral",
            "coolwarm": "CoolWarm",
            "hsv": "HSV"
        };

        // Load saved colormap selection
    const savedColormap = localStorage.getItem("selectedColormap") || "gray_r";
    colorPicker.value = savedColormap;
    colorPickerLabel.textContent = `Select Color Scheme: ${colormapNames[savedColormap]}`;

        // Listen for changes in color selection
    colorPicker.addEventListener("change", function () {
    const selectedColor = colorPicker.value;
    colorPickerLabel.textContent = `Select Color Scheme: ${colormapNames[selectedColor]}`;
    localStorage.setItem("selectedColormap", selectedColor);

            // Reload the page to apply the new colormap
            setTimeout(() => {
                location.reload(true);
            }, 100);
        });


    document.getElementById("input-form").addEventListener("submit", function(event) {
        event.preventDefault();  // Prevent form submission on Enter key press
    });
    document.getElementById("chat-input").addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();  // Prevent Enter key from submitting the form
        }
    });


    const MAX_CHAR_LIMIT = 150; // Adjust limit as needed

    inputField.addEventListener("input", function () {
        if (inputField.value.length > MAX_CHAR_LIMIT) {
            inputField.value = inputField.value.substring(0, MAX_CHAR_LIMIT); // Trim excess characters
        }
        
        // Show remaining characters dynamically
        const remainingChars = MAX_CHAR_LIMIT - inputField.value.length;
        document.getElementById("char-counter").textContent = `Characters remaining: ${remainingChars}`;
    });
    
    // Prevent paste if it exceeds limit
    inputField.addEventListener("paste", function (event) {
        let pastedText = (event.clipboardData || window.clipboardData).getData("text");
        if (inputField.value.length + pastedText.length > MAX_CHAR_LIMIT) {
            event.preventDefault(); // Stop pasting if it exceeds limit
        }
    });
    

    // Check if all elements exist before proceeding
    if (!inputField || !promptDisplay || !imageContainer || !colorPicker) {
        console.error(" Error: One or more required elements are missing in the DOM.");
        return; // Stop execution if elements are missing
    }

    const GAN_PROXY_URL = "https://web-service-ca2-daaa2b02-2309123.onrender.com/generate_image"; 
    let debounceTimer = null; // Prevent API spam
    let generatedImages = {}; // Store generated images { "A": base64Image, "B": base64Image, " ": blankImage }

      // Generate a blank 28x28 image based on colormap
function createBlankImage(cmap) {
    const canvas = document.createElement("canvas");
    canvas.width = 28;
    canvas.height = 28;
    const ctx = canvas.getContext("2d");

    // Assign white to light colormaps and black to dark colormaps
    const blankColor = ["gray_r", "Blues", "Greens", "Reds", "Purples"].includes(cmap) ? "white" : "black";

    console.log(`Colormap: ${cmap}, Selected Blank Color: ${blankColor}`);

    ctx.fillStyle = blankColor;
    ctx.fillRect(0, 0, 28, 28);

    return canvas.toDataURL("image/png").split(",")[1]; 
}


    function getSelectedColor() {
        return colorPicker ? colorPicker.value : "gray_r";
    }

    function updateBlankImage() {
        const selectedColor = getSelectedColor();
        generatedImages[" "] = createBlankImage(selectedColor);
    }

    updateBlankImage();

    colorPicker.addEventListener("change", function () {
        console.log(`🔹 Colormap changed to: ${colorPicker.value}`);
    
        // Save the selected colormap in localStorage
        localStorage.setItem("selectedColormap", colorPicker.value);
    
        // Reload the page after a short delay (optional to allow UI feedback)
        setTimeout(() => {
            location.reload(true);  // Force a hard refresh
        }, 100);  // Delay slightly so user sees the selection before reload
    }); 
    document.addEventListener("DOMContentLoaded", function () {
        const savedColormap = localStorage.getItem("selectedColormap") || "gray_r";  // Default
    
        // Restore selection
        colorPicker.value = savedColormap;
    
        // Apply colormap to button text
        updateColorButtonLabel(savedColormap);
    
        // Update images accordingly
        updateBlankImage();
        updateDisplayedImages(inputField.value.trim().toUpperCase());
    });
    
    function updateColorButtonLabel(selectedColormap) {
        const colormapNames = {
            "gray_r": "Black (Default)",
            "gray": "Inverse Background",
            "Blues": "Blue",
            "Greens": "Green",
            "Reds": "Red",
            "Purples": "Purple",
            "YlGnBu": "Yellow-Blue",
            "twilight": "Twilight",
            "inferno": "Inferno",
            "magma": "Magma",
            "plasma": "Plasma",
            "viridis": "Viridis",
            "cividis": "Cividis",
            "Spectral": "Spectral",
            "coolwarm": "CoolWarm",
            "hsv": "HSV"
        };
    
        // Get the button element
        const colorButton = document.getElementById("color-picker-button");
    
        if (colorButton) {
            colorButton.textContent = colormapNames[selectedColormap] || "Custom";
        }
    }
    

    inputField.addEventListener("input", function (event) {
        let text = inputField.value.trim().toUpperCase();
        if (!/^[A-Z\s]*$/.test(text)) {
            inputField.value = text.replace(/[^A-Z\s]/g, "");
            return;
        }

        updateTitle(text);

        if (event.inputType === "deleteContentBackward") {
            handleBackspace(text);
            return;
        }

        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            updateDisplayedImages(text);
        }, 300);
    });


    
    function updateTitle(text) {
        if (!text) {
            promptDisplay.style.display = "none";
        } else {
            promptDisplay.style.display = "block";
            promptDisplay.textContent = `Generated Letters for: "${text}"`;
            saveButton.style.display = "block";
        }
    }

    async function updateDisplayedImages(text) {
        if (!text) {
            imageContainer.innerHTML = ""; // Clear everything when input is empty
            generatedImages = { " ": createBlankImage() }; // Reset stored images, keep blank
            return;
        }

        const selectedColor = colorPicker ? colorPicker.value : "gray_r";
        console.log(`🔹 Updating images for: "${text}" with colormap "${selectedColor}"`);

        for (let letter of text) {
            if (!generatedImages[letter]) { // Only request new letters that haven't been generated
                generatedImages[letter] = letter === " " ? createBlankImage() : await generateSingleLetter(letter, selectedColor);
            }
        }

        renderImages(text); // Display stored images
    }

    function handleBackspace(text) {
        // Remove deleted letters from the stored images (except spaces)
        Object.keys(generatedImages).forEach((letter) => {
            if (!text.includes(letter) && letter !== " ") {
                delete generatedImages[letter];
            }
        });

        renderImages(text);
    }

    async function generateSingleLetter(letter, selectedColor) {
        const savedColormap = localStorage.getItem("selectedColormap") || selectedColor; // Use saved colormap
    
        try {
            const response = await fetch(GAN_PROXY_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: letter, cmap: savedColormap })
            });
    
            const data = await response.json();
            if (!data.success || !data.images || data.images.length === 0) {
                throw new Error(data.error || "Invalid response from server.");
            }
    
            console.log(` Image generated for letter: ${letter} with colormap: ${savedColormap}`);
            return data.images[0];
        } catch (error) {
            console.error(` Failed to generate image for ${letter}:`, error);
            return createBlankImage(savedColormap); // Ensure blank image uses correct colormap
        }
    }
    
    function renderImages(text) {
        imageContainer.innerHTML = ""; // Clear previous images only if needed

        for (let letter of text) {
            if (generatedImages[letter]) {
                const img = new Image();
                img.src = `data:image/png;base64,${generatedImages[letter]}`;
                img.classList.add("gen-image");
                img.alt = `Generated: ${letter}`;
                imageContainer.appendChild(img);
            }
        }
    }
    saveButton.addEventListener("click", async function () {
        let text = promptDisplay.textContent.replace("Generated Letters for: ", "").trim();
        text = text.replace(/^"|"$/g, ''); // Remove surrounding quotes
    
        if (!text) {
            alert("Invalid input! Please enter text.");
            return;
        }
    
        const selectedColor = colorPicker.value;

    
        try {
            // Step 1: Merge images before saving
            const base64Image = await mergeImagesForSaving(text);
    
            if (!base64Image) {
                alert("Error generating image!");
                return;
            }
    
            console.log("🔹 Sending Image Data:", base64Image.length > 100 ? base64Image.substring(0, 100) + "..." : base64Image);
    
            // Step 2: Send the merged image to the server
            const saveResponse = await fetch("/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text: text,
                    image: base64Image,  // Merged image
                    cmap: selectedColor  
                })
            });
    
            const data = await saveResponse.json();
            if (data.success) {
                alert(`Saved successfully!`);
            } else {
                console.error(" Save failed:", data.error);
                alert(`Error: ${data.error}`);
            }
    
        } catch (error) {
            console.error(" Failed to save:", error);
            alert("An error occurred while saving.");
        }
    });
    
    
    async function mergeImagesForSaving(text) {
        return new Promise((resolve) => {
            const canvas = document.createElement("canvas");
            const ctx = canvas.getContext("2d");
    
            const imgWidth = 28;
            const imgHeight = 28;
        
            const maxCharsPerRow = 20; // Max letters per row before wrapping
    
            const numRows = Math.ceil(text.length / maxCharsPerRow);
            const totalWidth = Math.min(text.length, maxCharsPerRow) * (imgWidth);
            const totalHeight = numRows * (imgHeight);
    
            canvas.width = totalWidth;
            canvas.height = totalHeight;
    
            let xOffset = 0;
            let yOffset = 0;
            let loadedImages = 0;
    
            text.split("").forEach((letter, index) => {
                const img = new Image();
                img.src = `data:image/png;base64,${generatedImages[letter]}`;
    
                img.onload = function () {
                    ctx.drawImage(img, xOffset, yOffset, imgWidth, imgHeight);
                    loadedImages++;
    
                    // Move to the next column
                    xOffset += imgWidth
    
                    // Wrap to a new row if maxCharsPerRow is reached
                    if ((index + 1) % maxCharsPerRow === 0) {
                        xOffset = 0;
                        yOffset += imgHeight;
                    }
    
                    // Resolve the promise once all images are loaded
                    if (loadedImages === text.length) {
                        console.log("Final merged sentence image ready for saving!");
                        resolve(canvas.toDataURL("image/png").split(",")[1]); // Convert to Base64
                    }
                };
            });
        });
    }
    

});
