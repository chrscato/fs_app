# Compensation Fee Schedule App

## Overview
The Compensation Fee Schedule App is a web application designed to help users understand the workers' compensation fee schedule, Medicare rates, and commercial payer rates. The application features an intuitive interface that allows users to upload a CMS-1500 form for processing. Utilizing Google OCR and the ChatGPT API, the app extracts relevant data and presents various rates in a user-friendly format.

## Features
- Upload CMS-1500 forms for processing.
- Extract data using Google OCR.
- Retrieve and display workers' compensation fee schedules, Medicare rates, and commercial payer rates.
- User-friendly design for easy navigation and understanding of rates.

## Project Structure
```
compensation-fee-schedule-app
├── public
│   ├── index.html
│   └── styles
│       └── main.css
├── src
│   ├── components
│   │   ├── App.js
│   │   ├── UploadForm.js
│   │   └── RatesDisplay.js
│   ├── services
│   │   ├── ocrService.js
│   │   └── apiService.js
│   ├── utils
│   │   └── helpers.js
│   └── index.js
├── package.json
├── .babelrc
├── .eslintrc.json
├── webpack.config.js
└── README.md
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd compensation-fee-schedule-app
   ```
3. Install the dependencies:
   ```
   npm install
   ```

## Usage
1. Start the development server:
   ```
   npm start
   ```
2. Open your browser and navigate to `http://localhost:3000` to access the application.
3. Use the upload form to submit a CMS-1500 form and view the extracted rates.

## Technologies Used
- React for building the user interface.
- Google OCR for text extraction from images.
- ChatGPT API for processing and interpreting extracted data.
- Webpack for module bundling.
- Babel for JavaScript transpilation.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.