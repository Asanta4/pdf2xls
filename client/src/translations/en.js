const translationsEN = {
  app: {
    title: 'PDF to Excel/CSV Converter',
    description: 'Upload a PDF file and convert tables to Excel or CSV format'
  },
  upload: {
    title: 'Upload PDF',
    dropzone: 'Drag and drop a PDF file here, or click to browse',
    processing: 'Processing...',
    uploadButton: 'Upload',
    invalidFile: 'Please upload a valid PDF file',
    maxSizeExceeded: 'File size exceeds the maximum limit of 10MB',
    uploadSuccess: 'File uploaded successfully!',
    uploadError: 'Error uploading file',
    limits: 'Maximum file size: 10MB, File type: PDF',
    button: 'Continue'
  },
  progress: {
    title: 'Conversion Progress',
    pending: 'Ready to convert',
    processing: 'Converting...',
    paused: 'Paused',
    completed: 'Conversion completed!',
    error: 'Error during conversion',
    analysis: 'Analyzing PDF structure...',
    page: 'Page',
    of: 'of',
    percent: '{percent}% Complete',
    completed: 'Complete'
  },
  conversion: {
    cancel: 'Cancel',
    pause: 'Pause',
    resume: 'Resume',
    start: 'Start Conversion',
    format: 'Format',
    csv: 'CSV',
    excel: 'Excel',
    title: 'Table Extraction',
    status: {
      completed: 'Successfully converted!',
      processing: 'Processing your file...',
      error: 'Conversion failed',
      pending: 'Pending',
      paused: 'Paused',
      completed: 'Completed',
      error: 'Error',
      processing: 'Processing',
      paused: 'Paused',
      completed: 'Completed',
    },
    download: 'Download your file',
    percent: '{percent}'
  },
  controls: {
    start: 'Start Conversion',
    pause: 'Pause',
    resume: 'Resume',
    cancel: 'Cancel',
    download: 'Download',
    downloadCSV: 'Download CSV',
    downloadExcel: 'Download Excel',
    chooseAnotherFile: 'Choose Another File'
  },
  preview: {
    title: 'Preview',
    showPreview: 'Show Preview',
    hidePreview: 'Hide Preview',
    noData: 'No preview data available',
    returnToFirstPage: 'Return to First Page'
  },
  download: {
    title: 'Your Conversion is Ready!',
    description: 'Choose the format you prefer to download your converted file.'
  },
  features: {
    title: 'Key Features',
    intelligentExtraction: 'Intelligent Table Extraction',
    intelligentExtractionDesc: 'Our advanced algorithms identify and extract tables from your PDF files with high accuracy.',
    rtlSupport: 'RTL Language Support',
    rtlSupportDesc: 'Full support for right-to-left languages such as Hebrew, ensuring proper text display and organization.',
    numberHandling: 'Smart Number Formatting',
    numberHandlingDesc: 'Automatic detection of numeric values, ensuring they appear as numbers in your Excel or CSV file.'
  },
  error: {
    generic: 'An error occurred',
    retry: 'Retry'
  },
  language: {
    en: 'English',
    he: 'Hebrew',
    switch: 'Change language'
  },
  footer: {
    help: 'Help',
    about: 'About'
  }
};

export default translationsEN; 