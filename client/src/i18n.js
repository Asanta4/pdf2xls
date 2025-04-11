import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';
import translationsEN from './translations/en';
import translationsHE from './translations/he';

i18n
  // Use HTTP backend for loading translations
  .use(Backend)
  // Detect user language
  .use(LanguageDetector)
  // Pass the i18n instance to react-i18next
  .use(initReactI18next)
  // Initialize i18next
  .init({
    resources: {
      en: {
        translation: translationsEN
      },
      he: {
        translation: translationsHE
      }
    },
    lng: 'en', // Default language
    fallbackLng: 'en',
    debug: process.env.NODE_ENV === 'development',
    
    interpolation: {
      escapeValue: false, // React already escapes values
    },
    
    // Configure backend for loading translation files
    backend: {
      loadPath: '/locales/{{lng}}/translation.json',
    },
    
    // RTL support
    react: {
      useSuspense: true,
    },
  });

// Function to update document direction based on language
export const updateDocumentDirection = (lng) => {
  // Set RTL for Hebrew, LTR for others
  document.documentElement.dir = lng === 'he' ? 'rtl' : 'ltr';
  document.documentElement.lang = lng;
};

// Set initial direction
updateDocumentDirection(i18n.language || 'en');

// Listen for language changes
i18n.on('languageChanged', (lng) => {
  updateDocumentDirection(lng);
});

export default i18n; 