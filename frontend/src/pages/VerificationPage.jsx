import React, { useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Search,
  ExternalLink,
  Copy,
  Check,
  Info,
  Smartphone,
  Printer,
  Building,
  Calendar,
  MapPin,
  Award
} from 'lucide-react';
import { CitationModal } from '../components/CitationModal';
import { LanguageSwitcher } from '../components/LanguageSwitcher';

const TRANSLATIONS = {
  en: {
    bannerBadge: "Bureau of Indian Standards Registry",
    bannerTitle: "BIS License & HUID Verification Console",
    bannerDesc: "Verify ISI Mark Certification Licenses (CM/L) and 6-character laser-engraved Hallmark Unique Identification (HUID) codes against official BIS conformity registries.",
    preferredLang: "Select Language",
    tabLicense: "BIS License (CM/L)",
    tabHUID: "Gold Hallmarking (HUID)",
    licenseHeading: "Verify ISI Certification Mark License (CM/L)",
    licenseDesc: "Enter the 7 or 8-digit CM/L number printed underneath the ISI logo on product packaging or marking plates (e.g., CM/L-4151201).",
    licensePlaceholder: "Enter license number (e.g. CM/L-4151201 or 4151201)",
    verifyLicenseBtn: "Verify License",
    huidHeading: "Verify Hallmark Unique Identification (HUID)",
    huidDesc: "Enter the 6-character alphanumeric code laser-engraved on gold or silver jewellery alongside the BIS hallmark triangle logo (e.g., A1B2C3).",
    huidPlaceholder: "Enter 6-character HUID (e.g. A1B2C3)",
    verifyHuidBtn: "Verify HUID",
    checkingBtn: "Verifying with Registry...",
    quickTest: "Authoritative Test Cases:",
    reportTitle: "Registry Verification Report",
    formatValid: "Format Valid",
    formatInvalid: "Invalid Format",
    statusVerified: "Operative & Valid",
    statusSuspicious: "Suspicious / Unregistered",
    statusExpired: "Expired",
    statusSuspended: "Suspended",
    nextStepTitle: "Official BIS Portal Cross-Verification",
    nextStepDesc: "For binding legal certification, manufacturer address validation, and official scope of license, verify directly on the BIS e-Services portal:",
    openPortalBtn: "Open Official BIS Portal",
    bisCareTitle: "BIS Care Official Consumer App",
    bisCareDesc: "Verify ISI mark licenses, scan QR codes on ISI-marked products, check HUID on gold jewellery instantly, and lodge formal consumer complaints directly with BIS.",
    bisCareBtn: "Learn about BIS Care",
    copied: "Copied",
    licenseFormatInvalidMsg: "The entered value does not conform to the standard BIS CM/L license format. A valid BIS license consists of 'CM/L-' followed by 7 or 8 digits (e.g., CM/L-4151201).",
    licenseFormatValidMsg: "Valid BIS CM/L License Number structure. Cross-verify operative status, brand endorsements, and validity dates on the official BIS portal.",
    huidFormatInvalidMsg: "The entered code is invalid. Mandatory BIS HUID must be exactly 6 alphanumeric characters (e.g., A1B2C3).",
    huidFormatValidMsg: "Valid 6-character Hallmark Unique Identification structure. Verify registered jeweller details, gold purity grade, and assaying centre on the BIS Care App."
  },
  hi: {
    bannerBadge: "भारतीय मानक ब्यूरो रजिस्ट्री",
    bannerTitle: "बीआईएस लाइसेंस एवं HUID सत्यापन कंसोल",
    bannerDesc: "नकली उत्पादों और जाली हॉलमार्किंग से सुरक्षा के लिए ISI लाइसेंस नंबर (CM/L) और 6-अक्षरीय हॉलमार्क विशिष्ट पहचान (HUID) का सत्यापन करें।",
    preferredLang: "भाषा चुनें",
    tabLicense: "बीआईएस लाइसेंस (CM/L)",
    tabHUID: "स्वर्ण हॉलमार्किंग (HUID)",
    licenseHeading: "ISI प्रमाणन चिह्न लाइसेंस (CM/L) सत्यापित करें",
    licenseDesc: "उत्पाद पैकेजिंग पर ISI लोगो के नीचे मुद्रित 7 या 8 अंकों का CM/L नंबर दर्ज करें (उदा. CM/L-4151201)।",
    licensePlaceholder: "लाइसेंस संख्या दर्ज करें (उदा. CM/L-4151201)",
    verifyLicenseBtn: "लाइसेंस सत्यापित करें",
    huidHeading: "हॉलमार्क विशिष्ट पहचान (HUID) सत्यापित करें",
    huidDesc: "सोने या चांदी के आभूषणों पर लेजर-उत्कीर्ण 6-अक्षरीय कोड दर्ज करें (उदा. A1B2C3)।",
    huidPlaceholder: "6-अक्षरीय HUID दर्ज करें (उदा. A1B2C3)",
    verifyHuidBtn: "HUID सत्यापित करें",
    checkingBtn: "रजिस्ट्री से जांच जारी है...",
    quickTest: "नमूना परीक्षण मामले:",
    reportTitle: "रजिस्ट्री सत्यापन रिपोर्ट",
    formatValid: "प्रारूप मान्य",
    formatInvalid: "प्रारूप अमान्य",
    statusVerified: "प्रमाणित एवं सक्रिय",
    statusSuspicious: "संदिग्ध / गैर-पंजीकृत",
    statusExpired: "समाप्त (Expired)",
    statusSuspended: "निलंबित (Suspended)",
    nextStepTitle: "आधिकारिक पोर्टल पर अंतिम सत्यापन",
    nextStepDesc: "निर्माता की स्थिति, ब्रांड विवरण और हॉलमार्क शुद्धता की पुष्टि के लिए आधिकारिक बीआईएस पोर्टल पर देखें:",
    openPortalBtn: "आधिकारिक बीआईएस पोर्टल खोलें",
    bisCareTitle: "बीआईएस केयर आधिकारिक मोबाइल ऐप",
    bisCareDesc: "उपभोक्ता ISI उत्पादों पर QR कोड स्कैन कर सकते हैं, सोने के आभूषणों पर HUID तुरंत सत्यापित कर सकते हैं और बीआईएस केयर ऐप के माध्यम से शिकायत दर्ज कर सकते हैं।",
    bisCareBtn: "BIS Care ऐप देखें",
    copied: "कॉपी किया गया",
    licenseFormatInvalidMsg: "दर्ज किया गया मान मानक बीआईएस CM/L लाइसेंस प्रारूप से मेल नहीं खाता है। वैध लाइसेंस में 'CM/L-' के बाद 7 या 8 अंक होते हैं (उदा. CM/L-4151201)।",
    licenseFormatValidMsg: "मान्य बीआईएस CM/L लाइसेंस संख्या संरचना। निर्माता की सक्रिय स्थिति और वैधता आधिकारिक बीआईएस पोर्टल पर जांचें।",
    huidFormatInvalidMsg: "दर्ज किया गया मान अमान्य है। अनिवार्य बीआईएस HUID ठीक 6 अक्षरों/अंकों का होना चाहिए (उदा. A1B2C3)।",
    huidFormatValidMsg: "मान्य 6-अक्षरीय हॉलमार्क विशिष्ट पहचान संरचना। पंजीकृत जौहरी, सोने की शुद्धता और केंद्र का विवरण बीआईएस केयर ऐप पर देखें।"
  },
  mr: {
    bannerBadge: "भारतीय मानक ब्युरो नोंदणी",
    bannerTitle: "BIS परवाना व HUID पडताळणी कन्सोल",
    bannerDesc: "बनावट उत्पादने आणि बनावट हॉलमार्किंगपासून संरक्षणासाठी ISI परवाना क्रमांक (CM/L) आणि 6-अंकी हॉलमार्क युनिक आयडेंटिफिकेशन (HUID) पडताळा.",
    preferredLang: "भाषा निवडा",
    tabLicense: "BIS परवाना (CM/L)",
    tabHUID: "सुवर्ण हॉलमार्किंग (HUID)",
    licenseHeading: "ISI प्रमाणन परवाना (CM/L) पडताळा",
    licenseDesc: "उत्पादनावरील ISI लोगोखाली छापलेला 7 किंवा 8 अंकी CM/L क्रमांक प्रविष्ट करा (उदा. CM/L-4151201).",
    licensePlaceholder: "परवाना क्रमांक प्रविष्ट करा (उदा. CM/L-4151201)",
    verifyLicenseBtn: "परवाना पडताळा",
    huidHeading: "हॉलमार्क युनिक आयडेंटिफिकेशन (HUID) पडताळा",
    huidDesc: "दागिन्यांवर लेझरने कोरलेला 6-अक्षरी अक्षरांकीत कोड प्रविष्ट करा (उदा. A1B2C3).",
    huidPlaceholder: "6-अक्षरी HUID प्रविष्ट करा (उदा. A1B2C3)",
    verifyHuidBtn: "HUID पडताळा",
    checkingBtn: "तपासत आहे...",
    quickTest: "चाचणी उदाहरणे:",
    reportTitle: "पडताळणी अहवाल",
    formatValid: "स्वरूप वैध",
    formatInvalid: "स्वरूप अवैध",
    statusVerified: "प्रमाणित वैध",
    statusSuspicious: "संशयास्पद / नोंदणी नसलेले",
    statusExpired: "कालबाह्य (Expired)",
    statusSuspended: "निलंबित (Suspended)",
    nextStepTitle: "अधिकृत पोर्टलवर पडताळणी",
    nextStepDesc: "उत्पादक माहिती, ब्रँड आणि हॉलमार्क शुद्धतेची खात्री करण्यासाठी अधिकृत BIS पोर्टलवर तपासा:",
    openPortalBtn: "अधिकृत BIS पोर्टल उघडा",
    bisCareTitle: "BIS Care अधिकृत मोबाईल ॲप",
    bisCareDesc: "ग्राहक ISI उत्पादनांवरील QR कोड स्कॅन करू शकतात आणि दागिन्यांवरील HUID त्वरित तपासू शकतात.",
    bisCareBtn: "BIS Care माहिती",
    copied: "कॉपी केले",
    licenseFormatInvalidMsg: "प्रविष्ट केलेले मूल्य मानक BIS CM/L परवाना स्वरूपाशी जुळत नाही (उदा. CM/L-4151201).",
    licenseFormatValidMsg: "वैध BIS CM/L परवाना क्रमांक रचना. अधिकृत BIS पोर्टलवर उत्पादकाची स्थिती आणि वैधता तपासा.",
    huidFormatInvalidMsg: "प्रविष्ट केलेले मूल्य अवैध आहे. अनिवार्य BIS HUID मध्ये नेमके 6 अक्षरे/अंक असावेत (उदा. A1B2C3).",
    huidFormatValidMsg: "वैध 6-अक्षरी HUID रचना. नोंदणीकृत सराफ, शुद्धता आणि हॉलमार्किंग केंद्र BIS Care ॲपवर तपासा."
  },
  ta: {
    bannerBadge: "இந்திய தரநிலைகள் பணியக பதிவேடு",
    bannerTitle: "BIS உரிமம் மற்றும் HUID சரிபார்ப்பு முனையம்",
    bannerDesc: "போலி தயாரிப்புகள் மற்றும் தரமற்ற ஹால்மார்க்கிங்கைத் தவிர்க்க ISI உரிம எண் (CM/L) மற்றும் 6-எழுத்து HUID குறியீட்டைச் சரிபார்க்கவும்.",
    preferredLang: "மொழியைத் தேர்ந்தெடுக்கவும்",
    tabLicense: "BIS உரிமம் (CM/L)",
    tabHUID: "தங்க ஹால்மார்க்கிங் (HUID)",
    licenseHeading: "ISI சான்றிதழ் உரிமத்தை (CM/L) சரிபார்க்கவும்",
    licenseDesc: "தயாரிப்பு பேக்கிங்கில் உள்ள ISI லோகோவின் கீழே அச்சிடப்பட்ட 7 அல்லது 8 இலக்க CM/L எண்ணை உள்ளிடவும் (எ.கா. CM/L-4151201).",
    licensePlaceholder: "உரிம எண் உள்ளிடவும் (எ.கா. CM/L-4151201)",
    verifyLicenseBtn: "உரிமத்தை சரிபார்க்கவும்",
    huidHeading: "ஹால்மார்க் தனித்துவ அடையாளத்தை (HUID) சரிபார்க்கவும்",
    huidDesc: "தங்க நகைகளில் லேசர் மூலம் பொறிக்கப்பட்ட 6 இலக்க எண்ணெழுத்து குறியீட்டை உள்ளிடவும் (எ.கா. A1B2C3).",
    huidPlaceholder: "6 இலக்க HUID உள்ளிடவும் (எ.கா. A1B2C3)",
    verifyHuidBtn: "HUID சரிபார்க்கவும்",
    checkingBtn: "சரிபார்க்கிறது...",
    quickTest: "மாதிரி சோதனைகள்:",
    reportTitle: "சரிபார்ப்பு அறிக்கை",
    formatValid: "வடிவம் சரியானது",
    formatInvalid: "தவறான வடிவம்",
    statusVerified: "சரிபார்க்கப்பட்டது",
    statusSuspicious: "சந்தேகத்திற்குரியது",
    statusExpired: "காலாவதியானது",
    statusSuspended: "இடைநீக்கம் செய்யப்பட்டது",
    nextStepTitle: "அதிகாரப்பூர்வ தள சரிபார்ப்பு",
    nextStepDesc: "உற்பத்தியாளர் விவரங்கள் மற்றும் தங்கத்தின் தூய்மையை உறுதிப்படுத்த அதிகாரப்பூர்வ BIS தளத்தில் பார்க்கவும்:",
    openPortalBtn: "அதிகாரப்பூர்வ BIS தளத்தை திறக்கவும்",
    bisCareTitle: "BIS Care மொபைல் செயலி",
    bisCareDesc: "நுகர்வோர் ISI தயாரிப்புகளின் QR குறியீடுகளை ஸ்கேன் செய்யவும், HUID குறியீட்டை உடனடியாக சரிபார்க்கவும் BIS Care செயலியைப் பயன்படுத்தலாம்.",
    bisCareBtn: "BIS Care பற்றி அறிய",
    copied: "நகலெடுக்கப்பட்டது",
    licenseFormatInvalidMsg: "உள்ளிடப்பட்ட எண் சரியான BIS CM/L வடிவத்தில் இல்லை (எ.கா. CM/L-4151201).",
    licenseFormatValidMsg: "சரியான BIS CM/L உரிம எண் வடிவம். BIS தளத்தில் உற்பத்தியாளர் நிலையை சரிபார்க்கவும்.",
    huidFormatInvalidMsg: "உள்ளிடப்பட்ட எண் தவறானது. கட்டாய BIS HUID சரியாக 6 எழுத்துகள்/எண்களைக் கொண்டிருக்க வேண்டும் (எ.கா. A1B2C3).",
    huidFormatValidMsg: "சரியான 6 இலக்க HUID வடிவம். நகைக்கடை மற்றும் தூய்மை விவரங்களை BIS Care செயலியில் சரிபார்க்கவும்."
  }
};

export default function VerificationPage() {
  const [activeTab, setActiveTab] = useState('license');
  const [licenseInput, setLicenseInput] = useState('');
  const [huidInput, setHuidInput] = useState('');
  const [language, setLanguage] = useState('en');
  const [isLoading, setIsLoading] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [copiedText, setCopiedText] = useState(null);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [showCitationModal, setShowCitationModal] = useState(false);

  const t = TRANSLATIONS[language] || TRANSLATIONS.en;

  const handleVerifyLicense = async (customVal) => {
    const val = (customVal || licenseInput).trim();
    if (!val || isLoading) return;

    if (customVal) setLicenseInput(customVal);
    setIsLoading(true);
    setVerificationResult(null);

    const cleanNo = val.toUpperCase().replace(/\s+/g, '');
    const isClientFormatValid = /^CM\/L-?\d{7,8}$/i.test(cleanNo) || /^\d{7,8}$/.test(cleanNo);
    const formattedLicenseId = cleanNo.startsWith('CM/L')
      ? (cleanNo.startsWith('CM/L-') ? cleanNo : cleanNo.replace('CM/L', 'CM/L-'))
      : `CM/L-${cleanNo}`;

    try {
      const response = await fetch('/verify/license', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_no: val })
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const data = await response.json();
      const isFormatValid = data.status !== 'invalid_format' && isClientFormatValid;

      setVerificationResult({
        type: 'license',
        query: val,
        formattedId: isFormatValid ? formattedLicenseId : val,
        isValidFormat: isFormatValid,
        status: data.status,
        details: data.details,
        message: data.message || (isFormatValid ? t.licenseFormatValidMsg : t.licenseFormatInvalidMsg),
        officialPortalUrl: "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/indian_standards/isdetails"
      });
    } catch (err) {
      console.warn("Backend fetch failed, using local format validation:", err);
      setVerificationResult({
        type: 'license',
        query: val,
        formattedId: isClientFormatValid ? formattedLicenseId : val,
        isValidFormat: isClientFormatValid,
        status: isClientFormatValid ? 'format_valid' : 'invalid_format',
        message: isClientFormatValid ? t.licenseFormatValidMsg : t.licenseFormatInvalidMsg,
        officialPortalUrl: "https://www.services.bis.gov.in/"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyHUID = async (customVal) => {
    const val = (customVal || huidInput).trim();
    if (!val || isLoading) return;

    if (customVal) setHuidInput(customVal);
    setIsLoading(true);
    setVerificationResult(null);

    const cleanHuid = val.toUpperCase().replace(/\s+/g, '');
    const isClientFormatValid = /^[A-Z0-9]{6}$/i.test(cleanHuid);

    try {
      const response = await fetch('/verify/huid', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ huid: val })
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const data = await response.json();
      const isFormatValid = data.status !== 'invalid_format' && isClientFormatValid;

      setVerificationResult({
        type: 'huid',
        query: val,
        formattedId: cleanHuid,
        isValidFormat: isFormatValid,
        status: data.status,
        details: data.details,
        message: data.message || (isFormatValid ? t.huidFormatValidMsg : t.huidFormatInvalidMsg),
        officialPortalUrl: "https://www.bis.gov.in/hallmarking/"
      });
    } catch (err) {
      console.warn("Backend HUID fetch failed, using local format validation:", err);
      setVerificationResult({
        type: 'huid',
        query: val,
        formattedId: cleanHuid,
        isValidFormat: isClientFormatValid,
        status: isClientFormatValid ? 'format_valid' : 'invalid_format',
        message: isClientFormatValid ? t.huidFormatValidMsg : t.huidFormatInvalidMsg,
        officialPortalUrl: "https://www.bis.gov.in/hallmarking/"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedText(text);
    setTimeout(() => setCopiedText(null), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Institutional Header Section */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                {t.bannerBadge}
              </span>
              <span className="text-xs text-slate-400 font-mono">Module 03</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              {t.bannerTitle}
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-2xl">
              {t.bannerDesc}
            </p>
          </div>

          <div className="shrink-0 pt-1">
            <LanguageSwitcher value={language} onChange={setLanguage} />
          </div>
        </div>
      </div>

      {/* Segmented Tab Navigation */}
      <div className="flex border-b border-slate-200 gap-2">
        <button
          type="button"
          onClick={() => {
            setActiveTab('license');
            setVerificationResult(null);
          }}
          className={`py-2.5 px-4 text-xs sm:text-sm font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-2 ${
            activeTab === 'license'
              ? 'border-slate-900 text-slate-900 bg-white rounded-t'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Award className="w-4 h-4" />
          <span>{t.tabLicense}</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setActiveTab('huid');
            setVerificationResult(null);
          }}
          className={`py-2.5 px-4 text-xs sm:text-sm font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-2 ${
            activeTab === 'huid'
              ? 'border-slate-900 text-slate-900 bg-white rounded-t'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>{t.tabHUID}</span>
        </button>
      </div>

      {/* License Tab Search Form */}
      {activeTab === 'license' && (
        <div className="bg-white border border-slate-200 rounded-lg p-5 sm:p-6 space-y-4 shadow-xs">
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-900">
              {t.licenseHeading}
            </h3>
            <p className="text-xs text-slate-500">
              {t.licenseDesc}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={licenseInput}
              onChange={(e) => setLicenseInput(e.target.value)}
              placeholder={t.licensePlaceholder}
              className="flex-1 px-3.5 py-2.5 bg-white border border-slate-300 rounded text-xs sm:text-sm font-mono text-slate-900 uppercase focus:border-slate-800 focus:ring-1 focus:ring-slate-800 outline-none transition"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleVerifyLicense();
                }
              }}
            />
            <button
              type="button"
              onClick={() => handleVerifyLicense()}
              disabled={!licenseInput.trim() || isLoading}
              className="px-5 py-2.5 bg-[#0b2545] hover:bg-[#081a31] text-white text-xs font-semibold rounded transition disabled:opacity-50 cursor-pointer flex items-center justify-center gap-1.5 shrink-0"
            >
              <Search className="w-3.5 h-3.5" />
              <span>{isLoading ? t.checkingBtn : t.verifyLicenseBtn}</span>
            </button>
          </div>

          {/* Quick Test Samples */}
          <div className="flex flex-wrap items-center gap-2 text-xs pt-1 border-t border-slate-100">
            <span className="text-slate-500 font-medium text-[11px]">{t.quickTest}</span>
            <button
              type="button"
              onClick={() => handleVerifyLicense('CM/L-4151201')}
              className="font-mono text-xs text-slate-700 bg-slate-100 hover:bg-slate-200 px-2 py-0.5 rounded border border-slate-200 cursor-pointer"
            >
              CM/L-4151201 (Steelbird Helmets)
            </button>
            <button
              type="button"
              onClick={() => handleVerifyLicense('CM/L-2347101')}
              className="font-mono text-xs text-slate-700 bg-slate-100 hover:bg-slate-200 px-2 py-0.5 rounded border border-slate-200 cursor-pointer"
            >
              CM/L-2347101 (Hawkins Cookers)
            </button>
            <button
              type="button"
              onClick={() => handleVerifyLicense('CM/L-8888888')}
              className="font-mono text-xs text-amber-800 bg-amber-50 hover:bg-amber-100 px-2 py-0.5 rounded border border-amber-200 cursor-pointer"
              title="Suspended status test"
            >
              CM/L-8888888 (Suspended)
            </button>
          </div>
        </div>
      )}

      {/* HUID Tab Search Form */}
      {activeTab === 'huid' && (
        <div className="bg-white border border-slate-200 rounded-lg p-5 sm:p-6 space-y-4 shadow-xs">
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-900">
              {t.huidHeading}
            </h3>
            <p className="text-xs text-slate-500">
              {t.huidDesc}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={huidInput}
              onChange={(e) => setHuidInput(e.target.value)}
              placeholder={t.huidPlaceholder}
              maxLength={6}
              className="flex-1 px-3.5 py-2.5 bg-white border border-slate-300 rounded text-xs sm:text-sm font-mono tracking-widest text-slate-900 uppercase focus:border-slate-800 focus:ring-1 focus:ring-slate-800 outline-none transition"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleVerifyHUID();
                }
              }}
            />
            <button
              type="button"
              onClick={() => handleVerifyHUID()}
              disabled={!huidInput.trim() || isLoading}
              className="px-5 py-2.5 bg-[#0b2545] hover:bg-[#081a31] text-white text-xs font-semibold rounded transition disabled:opacity-50 cursor-pointer flex items-center justify-center gap-1.5 shrink-0"
            >
              <Search className="w-3.5 h-3.5" />
              <span>{isLoading ? t.checkingBtn : t.verifyHuidBtn}</span>
            </button>
          </div>

          {/* Quick Test Samples */}
          <div className="flex flex-wrap items-center gap-2 text-xs pt-1 border-t border-slate-100">
            <span className="text-slate-500 font-medium text-[11px]">{t.quickTest}</span>
            <button
              type="button"
              onClick={() => handleVerifyHUID('A1B2C3')}
              className="font-mono text-xs text-slate-700 bg-slate-100 hover:bg-slate-200 px-2 py-0.5 rounded border border-slate-200 cursor-pointer"
            >
              A1B2C3 (22K Gold Bangle)
            </button>
            <button
              type="button"
              onClick={() => handleVerifyHUID('7R9P2X')}
              className="font-mono text-xs text-slate-700 bg-slate-100 hover:bg-slate-200 px-2 py-0.5 rounded border border-slate-200 cursor-pointer"
            >
              7R9P2X (18K Gold Chain)
            </button>
            <button
              type="button"
              onClick={() => handleVerifyHUID('XX00YY')}
              className="font-mono text-xs text-rose-800 bg-rose-50 hover:bg-rose-100 px-2 py-0.5 rounded border border-rose-200 cursor-pointer"
              title="Suspicious HUID test"
            >
              XX00YY (Suspicious)
            </button>
          </div>
        </div>
      )}

      {/* Verification Result Card - Official Verification Report Design */}
      {verificationResult && (
        <div className="bg-white border border-slate-300 rounded-lg shadow-sm overflow-hidden space-y-0">
          {/* Certificate Header Bar */}
          <div className="p-5 bg-slate-50 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div
                className={`w-9 h-9 rounded flex items-center justify-center shrink-0 border ${
                  verificationResult.isValidFormat
                    ? (verificationResult.details?.is_valid === false
                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                        : verificationResult.details?.status === 'SUSPENDED'
                        ? 'bg-amber-50 text-amber-800 border-amber-200'
                        : 'bg-emerald-50 text-emerald-800 border-emerald-200')
                    : 'bg-rose-50 text-rose-700 border-rose-200'
                }`}
              >
                {verificationResult.isValidFormat ? (
                  verificationResult.details?.is_valid === false ? (
                    <ShieldAlert className="w-5 h-5" />
                  ) : (
                    <ShieldCheck className="w-5 h-5" />
                  )
                ) : (
                  <ShieldAlert className="w-5 h-5" />
                )}
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                  {t.reportTitle}
                </span>
                <div className="text-base font-bold text-slate-900 font-mono flex items-center gap-2">
                  <span>{verificationResult.formattedId}</span>
                  {verificationResult.isValidFormat && (
                    <button
                      type="button"
                      onClick={() => copyToClipboard(verificationResult.formattedId)}
                      className="text-slate-400 hover:text-slate-700 p-0.5 transition cursor-pointer"
                      title={t.copied}
                    >
                      {copiedText === verificationResult.formattedId ? (
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span
                className={`px-2.5 py-1 rounded text-xs font-bold border ${
                  verificationResult.isValidFormat
                    ? (verificationResult.details?.status === 'SUSPENDED'
                        ? 'bg-amber-50 text-amber-800 border-amber-300'
                        : verificationResult.details?.status === 'EXPIRED'
                        ? 'bg-slate-100 text-slate-700 border-slate-300'
                        : verificationResult.details?.is_valid === false
                        ? 'bg-rose-50 text-rose-800 border-rose-300'
                        : 'bg-emerald-50 text-emerald-800 border-emerald-300')
                    : 'bg-rose-50 text-rose-800 border-rose-300'
                }`}
              >
                {verificationResult.isValidFormat
                  ? (verificationResult.details?.status === 'SUSPENDED'
                      ? t.statusSuspended
                      : verificationResult.details?.status === 'EXPIRED'
                      ? t.statusExpired
                      : verificationResult.details?.is_valid === false
                      ? t.statusSuspicious
                      : t.statusVerified)
                  : t.formatInvalid}
              </span>

              <button
                type="button"
                onClick={() => window.print()}
                className="px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 bg-white border border-slate-300 rounded hover:bg-slate-100 transition flex items-center gap-1 cursor-pointer no-print"
                title="Print official report"
              >
                <Printer className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Print</span>
              </button>
            </div>
          </div>

          {/* Details Body */}
          <div className="p-5 sm:p-6 space-y-4">
            <p className={`text-xs sm:text-sm leading-relaxed ${
              verificationResult.isValidFormat ? 'text-slate-700' : 'text-rose-700 font-medium'
            }`}>
              {verificationResult.message}
            </p>

            {/* License Details Table */}
            {verificationResult.details && verificationResult.details.manufacturer_name && (
              <div className="border border-slate-200 rounded overflow-hidden">
                <table className="w-full text-xs text-left">
                  <tbody className="divide-y divide-slate-200">
                    <tr className="bg-slate-50">
                      <th className="py-2.5 px-4 font-semibold text-slate-600 w-1/3">Licensee Entity:</th>
                      <td className="py-2.5 px-4 font-bold text-slate-900">{verificationResult.details.manufacturer_name}</td>
                    </tr>
                    <tr>
                      <th className="py-2.5 px-4 font-semibold text-slate-600">Brand Name:</th>
                      <td className="py-2.5 px-4 font-medium text-slate-800">{verificationResult.details.brand_name || 'N/A'}</td>
                    </tr>
                    <tr className="bg-slate-50">
                      <th className="py-2.5 px-4 font-semibold text-slate-600">Product & Standard:</th>
                      <td className="py-2.5 px-4 font-medium text-slate-800">{verificationResult.details.product_name} • <span className="font-mono font-semibold">{verificationResult.details.applicable_standard}</span></td>
                    </tr>
                    <tr>
                      <th className="py-2.5 px-4 font-semibold text-slate-600">Certification Scheme:</th>
                      <td className="py-2.5 px-4 font-medium text-slate-800">{verificationResult.details.scheme}</td>
                    </tr>
                    <tr className="bg-slate-50">
                      <th className="py-2.5 px-4 font-semibold text-slate-600">Validity Period:</th>
                      <td className="py-2.5 px-4 font-medium text-slate-800">{verificationResult.details.valid_from} to {verificationResult.details.valid_until}</td>
                    </tr>
                    <tr>
                      <th className="py-2.5 px-4 font-semibold text-slate-600">Manufacturing Facility:</th>
                      <td className="py-2.5 px-4 font-medium text-slate-800">{verificationResult.details.factory_address}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}

            {/* HUID Details Table */}
            {verificationResult.details && verificationResult.details.jeweller_name && (
              <div className="border border-slate-200 rounded overflow-hidden">
                <table className="w-full text-xs text-left">
                  <tbody className="divide-y divide-slate-200">
                    <tr className="bg-slate-50">
                      <th className="py-2.5 px-4 font-semibold text-slate-600 w-1/3">Registered Jeweller:</th>
                      <td className="py-2.5 px-4 font-bold text-slate-900">{verificationResult.details.jeweller_name}</td>
                    </tr>
                    <tr>
                      <th className="py-2.5 px-4 font-semibold text-slate-600">Jeweller Registration No:</th>
                      <td className="py-2.5 px-4 font-mono font-medium text-slate-800">{verificationResult.details.jeweller_registration_no || 'N/A'}</td>
                    </tr>
                    <tr className="bg-slate-50">
                      <th className="py-2.5 px-4 font-semibold text-slate-600">Purity & Article Description:</th>
                      <td className="py-2.5 px-4 font-bold text-slate-900">{verificationResult.details.purity} • {verificationResult.details.article_type}</td>
                    </tr>
                    <tr>
                      <th className="py-2.5 px-4 font-semibold text-slate-600">Assaying & Hallmarking Centre:</th>
                      <td className="py-2.5 px-4 font-medium text-slate-800">{verificationResult.details.ahc_name} (<span className="font-mono">{verificationResult.details.ahc_code}</span>)</td>
                    </tr>
                    <tr className="bg-slate-50">
                      <th className="py-2.5 px-4 font-semibold text-slate-600">Hallmarking Date & Weight:</th>
                      <td className="py-2.5 px-4 font-medium text-slate-800">{verificationResult.details.hallmarking_date} ({verificationResult.details.weight_grams} grams)</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}

            {/* Official Confirmation Box */}
            {verificationResult.isValidFormat && (
              <div className="p-4 bg-slate-50 rounded border border-slate-200 space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 uppercase tracking-wide">
                  <Info className="w-3.5 h-3.5 text-slate-700" />
                  <span>{t.nextStepTitle}</span>
                </div>
                <p className="text-xs text-slate-600">
                  {t.nextStepDesc}
                </p>
                <div className="pt-1">
                  <a
                    href={verificationResult.officialPortalUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#0b2545] hover:bg-[#081a31] text-white text-xs font-medium rounded transition"
                  >
                    <span>{t.openPortalBtn}</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* BIS Care Official Mobile App Information Box */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xs">
        <div className="flex items-start gap-3">
          <div className="p-2.5 bg-slate-100 text-slate-800 rounded border border-slate-200 shrink-0">
            <Smartphone className="w-5 h-5" />
          </div>
          <div className="space-y-0.5">
            <h3 className="text-sm font-bold text-slate-900">
              {t.bisCareTitle}
            </h3>
            <p className="text-xs text-slate-500 max-w-xl leading-relaxed">
              {t.bisCareDesc}
            </p>
          </div>
        </div>

        <a
          href="https://www.bis.gov.in/the-bureau/bis-care-app/"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded transition shrink-0"
        >
          <span>{t.bisCareBtn}</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>

      {/* Citations Modal */}
      <CitationModal
        show={showCitationModal}
        onClose={() => {
          setShowCitationModal(false);
          setSelectedCitation(null);
        }}
        citation={selectedCitation}
      />
    </div>
  );
}
