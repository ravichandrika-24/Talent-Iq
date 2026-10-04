```javascript
// Talent-IQ main JavaScript

document.addEventListener("DOMContentLoaded", function () {

    console.log("Talent-IQ loaded successfully.");

    const buttons = document.querySelectorAll(".btn");

    buttons.forEach(function (button) {

        button.addEventListener("click", function () {
            console.log("Talent-IQ navigation:", button.textContent.trim());
        });

    });

});
```
