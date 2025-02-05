document.addEventListener("DOMContentLoaded", function () {
    const inputField = document.getElementById("chat-input");
    const promptDisplay = document.getElementById("prompt-display");
    const imageDisplay = document.getElementById("generated-image");
    const saveButton = document.getElementById("save-button");

    let timeout = null;
    const GAN_PROXY_URL = "http://127.0.0.1:5000/proxy_generate"; // Using Flask proxy

    inputField.addEventListener("input", function () {
        let letter = inputField.value.toUpperCase();

        if (!/^[A-Z]$/.test(letter)) {
            inputField.value = "";
            return;
        }

        inputField.value = letter;

        clearTimeout(timeout);
        timeout = setTimeout(() => sendRequest(letter), 300);
    });

    async function sendRequest(letter) {
        try {


            const response = await fetch(GAN_PROXY_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: letter })
            });

            const data = await response.json();

            if (!data.success || !data.image) {
                throw new Error(data.error || "Invalid response from server.");
            }

            promptDisplay.style.display = "block";
            promptDisplay.textContent = `Generated Image for: "${letter}"`;
            imageDisplay.src = `data:image/png;base64,${data.image}`;
            imageDisplay.style.display = "block";
            saveButton.style.display = "block";

        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred while generating the image.");
        }
    }

    // Function to save generated image
    saveButton.addEventListener("click", async function () {
        if (!imageDisplay.src || imageDisplay.style.display === "none") {
            alert("No image to save!");
            return;
        }

        let letter = promptDisplay.textContent.replace("Generated Image for: ", "").trim();
        letter = letter.replace(/^"|"$/g, ''); // Remove surrounding quotes

        if (!/^[A-Z]$/.test(letter)) {
            alert("Invalid letter! Please enter a single letter from A-Z.");
            return;
        }

        // Step 2: Convert image to Base64
        try {
            const response = await fetch(imageDisplay.src);
            const blob = await response.blob();
            const reader = new FileReader();

            reader.readAsDataURL(blob);
            reader.onloadend = async function () {
                const base64Image = reader.result.split(",")[1]; // Extract base64 part

                // Step 3: Send letter and Base64 image to the server
                try {
                    const saveResponse = await fetch("/save", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ letter: letter, image: base64Image })
                    });

                    const data = await saveResponse.json();
                    if (data.success) {
                        alert(`Letter "${letter}" and its image saved successfully!`);
                    } else {
                        alert(`Error: ${data.error}`);
                    }
                } catch (error) {
                    console.error("Database request failed:", error);
                    alert("An error occurred while saving to the database.");
                }
            };
        } catch (error) {
            console.error("Failed to fetch image data:", error);
            alert("An error occurred while processing the image.");
        }
    });
});