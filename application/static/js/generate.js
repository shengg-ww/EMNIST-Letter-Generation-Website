document.addEventListener("DOMContentLoaded", function () {
    const inputField = document.getElementById("chat-input");
    const promptDisplay = document.getElementById("prompt-display");
    const imageContainer = document.getElementById("generated-images-container");
    const saveButton = document.getElementById("save-button");
    const colorPicker = document.getElementById("color-picker");

    document.getElementById("input-form").addEventListener("submit", function(event) {
        event.preventDefault();  // Prevent form submission on Enter key press
    });
    document.getElementById("chat-input").addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();  // Prevent Enter key from submitting the form
        }
    });

    document.getElementById("chat-input").addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();  // Prevent Enter key from submitting the form
        }
    });



    // Check if all elements exist before proceeding
    if (!inputField || !promptDisplay || !imageContainer || !colorPicker) {
        console.error("❌ Error: One or more required elements are missing in the DOM.");
        return; // Stop execution if elements are missing
    }

    const GAN_PROXY_URL = "http://127.0.0.1:5000/proxy_generate"; // Ensure it targets the correct backend route
    let debounceTimer = null; // Prevent API spam
    let generatedImages = {}; // Store generated images { "A": base64Image, "B": base64Image, " ": blankImage }

        // Generate a blank 28x28 image that matches the selected colormap (cmap)
    function createBlankImage(cmap) {
            const canvas = document.createElement("canvas");
            canvas.width = 28;
            canvas.height = 28;
            const ctx = canvas.getContext("2d");
        
            // Adjust blank color based on colormap
            let isInverted = cmap === "gray_r"; // 'gray_r' inverts colors (white text on black)
            let blankColor = isInverted ? "black" : "white"; 
        
            // Fill the entire canvas with the correct color
            ctx.fillStyle = blankColor;
            ctx.fillRect(0, 0, 28, 28);
        
            return canvas.toDataURL("image/png").split(",")[1]; // Convert to Base64 (remove prefix)
        }
        

    // Preload blank image for spaces
    generatedImages[" "] = createBlankImage();

    inputField.addEventListener("input", function (event) {
        let text = inputField.value.trim().toUpperCase();
        if (!/^[A-Z\s]*$/.test(text)) {
            inputField.value = text.replace(/[^A-Z\s]/g, ""); // Allow only letters and spaces
            return;
        }

        // Update the title dynamically
        updateTitle(text);

        if (event.inputType === "deleteContentBackward") {
            handleBackspace(text);
            return;
        }

        // Debounce input to avoid excessive API calls
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            updateDisplayedImages(text);
        }, 300); // Wait for 300ms after the last keystroke
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
        try {
            const response = await fetch(GAN_PROXY_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: letter, cmap: selectedColor })
            });

            const data = await response.json();
            if (!data.success || !data.images || data.images.length === 0) {
                throw new Error(data.error || "Invalid response from server.");
            }

            console.log(`✔ Image generated for letter: ${letter}`);
            return data.images[0]; // Return first image
        } catch (error) {
            console.error(`❌ Failed to generate image for ${letter}:`, error);
            return createBlankImage(); // Fallback to blank image if there's an error
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
                console.error("❌ Save failed:", data.error);
                alert(`Error: ${data.error}`);
            }
    
        } catch (error) {
            console.error("❌ Failed to save:", error);
            alert("An error occurred while saving.");
        }
    });
    
    // Function to merge letter images into a single image before saving
    async function mergeImagesForSaving(text) {
        return new Promise((resolve) => {
            const canvas = document.createElement("canvas");
            const ctx = canvas.getContext("2d");
    
            const imgWidth = 28;
            const imgHeight = 28;
            const spacing = 3; 
    
            const totalWidth = text.length * (imgWidth + spacing) - spacing;
            canvas.width = totalWidth;
            canvas.height = imgHeight;
    
            let xOffset = 0;
            let loadedImages = 0;
    
            text.split("").forEach((letter) => {
                const img = new Image();
                img.src = `data:image/png;base64,${generatedImages[letter]}`;
    
                img.onload = function () {
                    ctx.drawImage(img, xOffset, 0, imgWidth, imgHeight);
                    xOffset += imgWidth + spacing;
                    loadedImages++;
    
                    if (loadedImages === text.length) {
                        console.log("✅ Final merged sentence image ready for saving!");
                        resolve(canvas.toDataURL("image/png").split(",")[1]); // Convert to Base64
                    }
                };
            });
        });
    }
    

});
