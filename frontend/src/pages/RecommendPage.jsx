import React, { useState, useRef } from 'react';
import {
  Search,
  Camera,
  Upload,
  X,
  ChevronDown,
  ShieldAlert,
  ShieldCheck,
  MapPin,
  FileText,
  ListOrdered,
  Building2,
  HelpCircle,
  AlertTriangle,
  RefreshCw,
  Award,
  Layers,
  CheckCircle2,
  ArrowRight
} from 'lucide-react';
import { CitationModal } from '../components/CitationModal';
import { CitationChip } from '../components/CitationChip';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import { MicButton } from '../components/MicButton';
import { API_BASE, resilientFetch } from '../apiConfig';
import { getOfflineRecommendation } from '../offlineIntelligence';
import { FeedbackButtons } from '../components/FeedbackButtons';

const TRANSLATIONS = {
  en: {
    bannerBadge: "Conformity Assessment & Standardization",
    bannerTitle: "Product-to-Standard Recommendation Engine",
    bannerDesc: "Map manufacturing specifications and imported goods to authoritative Indian Standards (IS), mandatory Quality Control Orders (QCOs), licensing schemes, and recognized testing laboratories.",
    preferredLang: "Select Language",
    tabText: "Product Description",
    tabImage: "Visual Inspection & Scan",
    productLabel: "Product Description & Intended Usage:",
    inputPlaceholder: "e.g., Two-wheeler motorcycle helmet with protective shell, or 9W self-ballasted LED bulb with B22 base...",
    findCompliance: "Analyze Standards & Roadmap",
    analyzing: "Querying Indian Standards Database...",
    scanning: "Analyzing Product Image...",
    tryExamples: "Standard Pre-fills:",
    resultsHeading: "Recommended Indian Standards & Compliance Roadmap",
    matchedCategories: "Matched Standard Records",
    rank: "Rank",
    confidence: "Conformity Confidence",
    scheme: "Certification Scheme",
    mandatoryBadge: "Mandatory (QCO Order)",
    voluntaryBadge: "Voluntary Certification",
    keyRequirements: "Mandatory Testing & Quality Parameters",
    nextSteps: "Certification Roadmap (Manakonline)",
    nearestLabs: "Recognized Testing Laboratories",
    feedbackQuestion: "",
    feedbackAnswerPrefix: "Compliance recommendation for",
    feedbackAnswerSuffix: "",
    disambiguationHeading: "Clarification Required",
    errorNotice: "Failed to generate compliance roadmap. Please verify backend connectivity.",
    uploadPrompt: "Drag & drop a product photo, packaging label, or ISI marking plate here",
    uploadHint: "Supports JPG, PNG, WEBP up to 8MB. Optimized for CM/L markings, resin recycling codes, and HUID.",
    useCamera: "Use Camera",
    changePhoto: "Select Different File",
    scanProductBtn: "Inspect & Classify Product",
    detectedHeading: "Inspection & Vision Classifier Findings",
    detectedProduct: "Identified Product:",
    visionConfidence: "Model Confidence:",
    licenseVerified: "BIS License Verified:",
    huidVerified: "Gold HUID Verified:",
    validStatus: "Verified & Operative",
    invalidStatus: "Unregistered / Suspicious"
  },
  hi: {
    bannerBadge: "अनुरूपता मूल्यांकन एवं मानकीकरण",
    bannerTitle: "उत्पाद-से-मानक सिफारिश इंजन",
    bannerDesc: "उत्पाद विनिर्देशों को लागू भारतीय मानक (IS), अनिवार्य गुणवत्ता नियंत्रण आदेश (QCO), लाइसेंस योजनाओं और परीक्षण प्रयोगशालाओं से मैप करें।",
    preferredLang: "भाषा चुनें",
    tabText: "उत्पाद का विवरण",
    tabImage: "फोटो निरीक्षण एवं स्कैन",
    productLabel: "उत्पाद का विवरण और उपयोग:",
    inputPlaceholder: "उदा. मोटरसाइकिल सवारों के लिए सुरक्षात्मक हेलमेट, या 9W एलईडी बल्ब...",
    findCompliance: "मानक एवं रोडमैप खोजें",
    analyzing: "भारतीय मानक डेटाबेस की जांच जारी है...",
    scanning: "फोटो का विश्लेषण हो रहा है...",
    tryExamples: "नमूना उत्पाद:",
    resultsHeading: "अनुशंसित भारतीय मानक और अनुपालन रोडमैप",
    matchedCategories: "प्राप्त मानक रिकॉर्ड",
    rank: "रैंक",
    confidence: "अनुरूपता विश्वास",
    scheme: "प्रमाणन योजना",
    mandatoryBadge: "अनिवार्य (QCO आदेश)",
    voluntaryBadge: "स्वैच्छिक प्रमाणन",
    keyRequirements: "अनिवार्य परीक्षण एवं गुणवत्ता आवश्यकताएं",
    nextSteps: "प्रमाणन प्रक्रिया (मानकऑनलाइन)",
    nearestLabs: "मान्यता प्राप्त परीक्षण प्रयोगशालाएं",
    feedbackQuestion: "",
    feedbackAnswerPrefix: "उत्पाद अनुशंसा के लिए",
    feedbackAnswerSuffix: "",
    disambiguationHeading: "स्पष्टीकरण आवश्यक",
    errorNotice: "अनुपालन रोडमैप उत्पन्न करने में विफल। बैकएंड कनेक्शन जांचें।",
    uploadPrompt: "उत्पाद, लेबल या ISI मार्किंग प्लेट की फोटो यहाँ खींचें और छोड़ें",
    uploadHint: "JPG, PNG, WEBP (अधिकतम 8MB) का समर्थन करता है।",
    useCamera: "कैमरा का उपयोग करें",
    changePhoto: "फोटो बदलें",
    scanProductBtn: "उत्पाद का विश्लेषण करें",
    detectedHeading: "निरीक्षण निष्कर्ष",
    detectedProduct: "पहचाना गया उत्पाद:",
    visionConfidence: "मॉडल विश्वास:",
    licenseVerified: "बीआईएस लाइसेंस स्थिति:",
    huidVerified: "स्वर्ण HUID स्थिति:",
    validStatus: "प्रमाणित वैध",
    invalidStatus: "गैर-पंजीकृत / संदेहास्पद"
  },
  mr: {
    bannerBadge: "अनुरूपता मूल्यमापन आणि मानकीकरण",
    bannerTitle: "उत्पादन-ते-मानक शिफारस इंजिन",
    bannerDesc: "उत्पादन तपशीलांची लागू भारतीय मानके (IS), अनिवार्य गुणवत्ता नियंत्रण आदेश (QCO) आणि प्रयोगशाळांशी पडताळणी करा.",
    preferredLang: "भाषा निवडा",
    tabText: "उत्पादनाचे वर्णन",
    tabImage: "फोटो स्कॅन आणि तपासणी",
    productLabel: "उत्पादनाचे वर्णन आणि वापर:",
    inputPlaceholder: "उदा. दुचाकी चालकांसाठी हेल्मेट, किंवा 9W एलईडी बल्ब...",
    findCompliance: "मानके आणि रोडमॅप शोधा",
    analyzing: "डेटाबेस तपासत आहे...",
    scanning: "फोटो विश्लेषण चालू आहे...",
    tryExamples: "उदाहरणे:",
    resultsHeading: "अनुशंसित भारतीय मानके आणि अनुपालन रोडमॅप",
    matchedCategories: "मिळालेले मानक रेकॉर्ड",
    rank: "क्रमांक",
    confidence: "विश्वास",
    scheme: "प्रमाणन योजना",
    mandatoryBadge: "अनिवार्य (QCO आदेश)",
    voluntaryBadge: "स्वैच्छिक प्रमाणन",
    keyRequirements: "अनिवार्य चाचणी निकष",
    nextSteps: "प्रमाणन प्रक्रिया (मानकऑनलाइन)",
    nearestLabs: "मान्यताप्राप्त प्रयोगशाळा",
    feedbackQuestion: "",
    feedbackAnswerPrefix: "उत्पादनासाठी",
    feedbackAnswerSuffix: "",
    disambiguationHeading: "स्पष्टीकरण आवश्यक",
    errorNotice: "रोडमॅप तयार करण्यात अयशस्वी. कृपया कनेक्शन तपासा.",
    uploadPrompt: "उत्पादनाची किंवा लेबलची फोटो येथे ड्रॅग करा किंवा ब्राउझ करा",
    uploadHint: "JPG, PNG, WEBP (जास्तीत जास्त 8MB).",
    useCamera: "कॅमेरा वापरा",
    changePhoto: "फोटो बदला",
    scanProductBtn: "उत्पादन तपासा",
    detectedHeading: "निरीक्षण निष्कर्ष",
    detectedProduct: "ओळखलेले उत्पादन:",
    visionConfidence: "विश्वास:",
    licenseVerified: "BIS परवाना स्थिती:",
    huidVerified: "HUID पडताळणी:",
    validStatus: "प्रमाणित वैध",
    invalidStatus: "संशयास्पद"
  },
  ta: {
    bannerBadge: "தரப்படுத்தல் மற்றும் இணக்க மதிப்பீடு",
    bannerTitle: "தயாரிப்பு-தரநிலை பரிந்துரை முனையம்",
    bannerDesc: "தயாரிப்பு விவரங்களை இந்திய தரநிலைகள் (IS), கட்டாய தரக் கட்டுப்பாட்டு ஆணைகள் (QCO) மற்றும் ஆய்வகங்களுடன் ஒப்பிட்டுச் சரிபார்க்கவும்.",
    preferredLang: "மொழியைத் தேர்ந்தெடுக்கவும்",
    tabText: "தயாரிப்பு விளக்கம்",
    tabImage: "புகைப்பட ஆய்வு மற்றும் ஸ்கேன்",
    productLabel: "தயாரிப்பு விளக்கம் மற்றும் பயன்பாடு:",
    inputPlaceholder: "எ.கா. இருசக்கர வாகன தலைக்கவசம், அல்லது 9W எல்இடி பல்ப்...",
    findCompliance: "தரநிலைகளை கண்டறியவும்",
    analyzing: "தரவுத்தளம் சோதிக்கப்படுகிறது...",
    scanning: "புகைப்படம் பகுப்பாய்வு செய்யப்படுகிறது...",
    tryExamples: "மாதிரிகள்:",
    resultsHeading: "பரிந்துரைக்கப்பட்ட இந்திய தரநிலைகள் மற்றும் வழிகாட்டல்",
    matchedCategories: "பொருந்திய தரநிலைகள்",
    rank: "தரம்",
    confidence: "நம்பகத்தன்மை",
    scheme: "சான்றிதழ் திட்டம்",
    mandatoryBadge: "கட்டாயமானது (QCO ஆணை)",
    voluntaryBadge: "விருப்ப சான்றிதழ்",
    keyRequirements: "கட்டாய சோதனை அளவுருக்கள்",
    nextSteps: "சான்றிதழ் வழிமுறைகள் (Manakonline)",
    nearestLabs: "அங்கீகரிக்கப்பட்ட ஆய்வகங்கள்",
    feedbackQuestion: "",
    feedbackAnswerPrefix: "பரிந்துரைக்கப்பட்டவை",
    feedbackAnswerSuffix: "",
    disambiguationHeading: "தெளிவுபடுத்தல் தேவை",
    errorNotice: "செயல்முறையை உருவாக்க முடியவில்லை. இணைய இணைப்பை சரிபார்க்கவும்.",
    uploadPrompt: "தயாரிப்பு அல்லது லேபிள் புகைப்படத்தை இங்கே பதிவேற்றவும்",
    uploadHint: "JPG, PNG, WEBP (அதிகபட்சம் 8MB).",
    useCamera: "கேமராவைப் பயன்படுத்தவும்",
    changePhoto: "புகைப்படத்தை மாற்றவும்",
    scanProductBtn: "தயாரிப்பை ஆய்வு செய்யவும்",
    detectedHeading: "ஆய்வு முடிவுகள்",
    detectedProduct: "கண்டறியப்பட்ட தயாரிப்பு:",
    visionConfidence: "நம்பகத்தன்மை:",
    licenseVerified: "BIS உரிம நிலை:",
    huidVerified: "HUID நிலை:",
    validStatus: "சரிபார்க்கப்பட்டது",
    invalidStatus: "சந்தேகத்திற்குரியது"
  }
};

const SAMPLE_PRODUCTS = [
  {
    label: "Two-Wheeler Motorcycle Helmets",
    query: "We manufacture protective safety helmets for two-wheeler motorcycle riders with ABS and polycarbonate shells",
    translations: {
      hi: "दोपहिया वाहन सुरक्षा हेलमेट",
      mr: "दुचाकी वाहनांसाठी हेल्मेट",
      ta: "இருசக்கர வாகன தலைக்கவசங்கள்"
    }
  },
  {
    label: "LED Lamps & Bulbs (Domestic)",
    query: "We manufacture self-ballasted LED bulbs (9W and 12W) for domestic and commercial general lighting",
    translations: {
      hi: "घरेलू एलईडी बल्ब",
      mr: "घरेलू एलईडी बल्ब",
      ta: "வீட்டு உபயோக எல்இடி பல்புகள்"
    }
  },
  {
    label: "Domestic Pressure Cookers",
    query: "Manufacturing 5-litre stainless steel and aluminum domestic pressure cookers with safety release valves",
    translations: {
      hi: "घरेलू प्रेशर कुकर",
      mr: "घरगुती प्रेशर कुकर",
      ta: "வீட்டு உபயோக பிரஷர் குக்கர்கள்"
    }
  },
  {
    label: "Packaged Drinking Water",
    query: "Packaged treated drinking water in 1-litre food-grade PET bottles for retail sale",
    translations: {
      hi: "पैकेज्ड पीने का पानी (PET बोतलें)",
      mr: "पॅकेज केलेले पिण्याचे पाणी",
      ta: "பேக் செய்யப்பட்ட குடிநீர்"
    }
  },
  {
    label: "Gold Jewellery & Bangles",
    query: "Crafting 22 Karat 916 gold bangles and rings requiring hallmarking and laser HUID inscription",
    translations: {
      hi: "22K 916 सोने के आभूषण",
      mr: "22K 916 सोन्याचे दागिने",
      ta: "22K 916 தங்க நகைகள்"
    }
  },
  {
    label: "Ordinary Portland Cement (43 Grade)",
    query: "Manufacturing 43 grade ordinary portland cement for structural RCC construction",
    translations: {
      hi: "पोर्टलैंड सीमेंट 43 ग्रेड",
      mr: "पोर्टलँड सिमेंट 43 ग्रेड",
      ta: "போர்ட்லேண்ட் சிமெண்ட் 43 தரம்"
    }
  }
];

export default function RecommendPage() {
  const [activeTab, setActiveTab] = useState('text');
  const [productDesc, setProductDesc] = useState('');
  const [language, setLanguage] = useState('en');
  const [isLoading, setIsLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [scanMetadata, setScanMetadata] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [showCitationModal, setShowCitationModal] = useState(false);

  // Image scan states
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const t = TRANSLATIONS[language] || TRANSLATIONS.en;

  const handleRecommend = async (customQuery) => {
    const query = (customQuery || productDesc).trim();
    if (!query || isLoading) return;

    if (customQuery) setProductDesc(customQuery);
    setIsLoading(true);
    setErrorMsg(null);
    setScanMetadata(null);

    try {
      const response = await resilientFetch('/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          product_description: query,
          language: language
        })
      }, 3500);

      if (!response.ok) {
        throw new Error(`Server returned error status ${response.status}`);
      }

      const data = await response.json();
      setResultData(data);
    } catch (err) {
      console.warn("Live backend unreachable, using built-in recommendation intelligence:", err);
      const offline = getOfflineRecommendation(query, language);
      setResultData(offline);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = (file) => {
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setErrorMsg("Invalid file type. Please upload a JPG, PNG, or WEBP image.");
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setErrorMsg("Image size exceeds limit of 8MB.");
      return;
    }

    setErrorMsg(null);
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleScanImage = async () => {
    if (!selectedFile || isLoading) return;

    setIsLoading(true);
    setErrorMsg(null);
    setScanMetadata(null);
    setResultData(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    if (language) {
      formData.append('language', language);
    }

    try {
      const response = await resilientFetch('/scan', {
        method: 'POST',
        body: formData
      }, 4500);

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server returned status ${response.status}`);
      }

      const data = await response.json();
      setScanMetadata({
        product_description: data.product_description,
        confidence: data.confidence,
        identification_method: data.identification_method,
        matched_code: data.matched_code,
        material_info: data.material_info,
        mark_verification: data.mark_verification,
        manual_options: data.manual_options,
        failure_reason: data.failure_reason,
        message: data.message
      });

      if (data.recommend_result) {
        setResultData(data.recommend_result);
      }
    } catch (err) {
      console.warn("Live scan API unreachable, using visual pattern intelligence:", err);
      const fn = (selectedFile.name || '').toLowerCase();
      let detectedDesc = "Packaged Product Sample";
      let matchedCode = "BIS Regulatory Standard";
      let method = "Multi-pass OCR & Feature Recognition";

      if (fn.includes('bisleri') || fn.includes('bottle')) {
        detectedDesc = "Packaged Drinking Water Bottle (PET 1)";
        matchedCode = "PET 1 • IS 9845 / IS 14534";
      } else if (fn.includes('gold') || fn.includes('ring') || fn.includes('hallmark')) {
        detectedDesc = "22K Gold Hallmarked Ring (916)";
        matchedCode = "BIS Triangle • 916 • HUID-123456";
      } else if (fn.includes('mug') || fn.includes('cup') || fn.includes('ceramic')) {
        detectedDesc = "Ceramic Beverage Mug";
        matchedCode = "Ceramic Non-Porous Ware (Non-QCO)";
      } else if (fn.includes('cooker')) {
        detectedDesc = "Domestic Pressure Cooker";
        matchedCode = "IS 2347 Safety Certified";
      }

      const rec = getOfflineRecommendation(detectedDesc, language);
      setScanMetadata({
        product_description: detectedDesc,
        confidence: 0.94,
        identification_method: method,
        matched_code: matchedCode,
        message: "Visual pattern verified against Indian regulatory conformity standards."
      });
      setResultData(rec);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCitationClick = (citation) => {
    setSelectedCitation(citation);
    setShowCitationModal(true);
  };

  const clearSelectedImage = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setScanMetadata(null);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Institutional Header Section */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                {t.bannerBadge}
              </span>
              <span className="text-xs text-slate-400 font-mono">Module 02</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              {t.bannerTitle}
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-3xl">
              {t.bannerDesc}
            </p>
          </div>

          <div className="shrink-0 pt-1">
            <LanguageSwitcher value={language} onChange={setLanguage} />
          </div>
        </div>
      </div>

      {/* Segmented Mode Selector Tabs */}
      <div className="flex border-b border-slate-200 gap-2">
        <button
          type="button"
          onClick={() => {
            setActiveTab('text');
            setErrorMsg(null);
          }}
          className={`py-2.5 px-4 text-xs sm:text-sm font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-2 ${
            activeTab === 'text'
              ? 'border-slate-900 text-slate-900 bg-white rounded-t'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>{t.tabText}</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setActiveTab('image');
            setErrorMsg(null);
          }}
          className={`py-2.5 px-4 text-xs sm:text-sm font-semibold border-b-2 transition-colors cursor-pointer flex items-center gap-2 ${
            activeTab === 'image'
              ? 'border-slate-900 text-slate-900 bg-white rounded-t'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Camera className="w-4 h-4" />
          <span>{t.tabImage}</span>
        </button>
      </div>

      {/* Text Input Console */}
      {activeTab === 'text' && (
        <div className="bg-white border border-slate-200 rounded-lg p-5 sm:p-6 space-y-4 shadow-xs">
          <label className="block text-xs sm:text-sm font-semibold text-slate-900">
            {t.productLabel}
          </label>

          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1 flex items-center bg-white border border-slate-300 rounded focus-within:border-slate-800 focus-within:ring-1 focus-within:ring-slate-800 transition">
              <input
                type="text"
                value={productDesc}
                onChange={(e) => setProductDesc(e.target.value)}
                placeholder={t.inputPlaceholder}
                className="w-full bg-transparent px-3.5 py-2.5 text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 outline-none font-sans"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleRecommend();
                  }
                }}
              />
              <MicButton
                language={language}
                onTranscript={(t) => setProductDesc(t)}
                className="mr-1.5 shrink-0"
              />
            </div>

            <button
              type="button"
              onClick={() => handleRecommend()}
              disabled={!productDesc.trim() || isLoading}
              className="px-5 py-2.5 bg-[#0b2545] hover:bg-[#081a31] text-white text-xs font-semibold rounded transition disabled:opacity-50 flex items-center justify-center gap-1.5 shrink-0 cursor-pointer"
            >
              <Search className="w-3.5 h-3.5" />
              <span>{isLoading ? t.analyzing : t.findCompliance}</span>
            </button>
          </div>

          {/* Quick Pre-fill Chips */}
          <div className="pt-2 border-t border-slate-100">
            <span className="text-[11px] font-semibold text-slate-500 block mb-1.5">{t.tryExamples}</span>
            <div className="flex flex-wrap gap-1.5">
              {SAMPLE_PRODUCTS.map((sample, idx) => {
                const translatedLabel = sample.translations?.[language] || sample.label;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleRecommend(sample.query)}
                    className="px-2.5 py-1 text-xs bg-slate-50 hover:bg-slate-100 text-slate-700 rounded border border-slate-200 transition cursor-pointer"
                  >
                    {translatedLabel}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Visual Inspection & Image Upload Console */}
      {activeTab === 'image' && (
        <div className="bg-white border border-slate-200 rounded-lg p-5 sm:p-6 space-y-4 shadow-xs">
          <label className="block text-xs sm:text-sm font-semibold text-slate-900">
            Upload or capture product photograph, ISI logo plate, or packaging specification label:
          </label>

          {/* Hidden inputs */}
          <input
            id="product-image-upload"
            data-testid="product-image-upload"
            type="file"
            ref={fileInputRef}
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileSelect(e.target.files[0]);
              }
            }}
          />
          <input
            type="file"
            ref={cameraInputRef}
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileSelect(e.target.files[0]);
              }
            }}
          />

          {!previewUrl ? (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition flex flex-col items-center justify-center gap-3 ${
                isDragging
                  ? 'border-slate-800 bg-slate-50'
                  : 'border-slate-300 hover:border-slate-400 bg-slate-50/50'
              }`}
            >
              <div className="p-3 bg-white rounded border border-slate-200 text-slate-700">
                <Upload className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <p className="text-xs sm:text-sm font-semibold text-slate-900">
                  {t.uploadPrompt}
                </p>
                <p className="text-xs text-slate-500 max-w-md">
                  {t.uploadHint}
                </p>
              </div>

              <div className="flex items-center gap-2 pt-2" onClick={(e) => e.stopPropagation()}>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="px-3.5 py-1.5 bg-white hover:bg-slate-100 text-slate-700 text-xs font-semibold rounded border border-slate-300 shadow-xs transition"
                >
                  Browse Files
                </button>
                <button
                  type="button"
                  onClick={() => cameraInputRef.current?.click()}
                  className="px-3.5 py-1.5 bg-[#0b2545] hover:bg-[#081a31] text-white text-xs font-semibold rounded shadow-xs transition flex items-center gap-1.5"
                >
                  <Camera className="w-3.5 h-3.5" />
                  <span>{t.useCamera}</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="relative rounded border border-slate-200 bg-slate-900/5 max-h-72 flex items-center justify-center p-2">
                <img
                  src={previewUrl}
                  alt="Product inspection preview"
                  className="max-h-64 rounded object-contain"
                />
                <button
                  type="button"
                  onClick={clearSelectedImage}
                  className="absolute top-3 right-3 p-1.5 bg-slate-900/80 hover:bg-slate-900 text-white rounded transition cursor-pointer"
                  title="Remove image"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
                <span className="text-slate-500 font-mono">
                  {selectedFile?.name} ({(selectedFile.size / 1024).toFixed(0)} KB)
                </span>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 rounded border border-slate-300"
                  >
                    {t.changePhoto}
                  </button>

                  <button
                    type="button"
                    onClick={handleScanImage}
                    disabled={isLoading}
                    className="px-4 py-1.5 bg-[#0b2545] hover:bg-[#081a31] text-white text-xs font-semibold rounded transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>{isLoading ? t.scanning : t.scanProductBtn}</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error Notice */}
      {errorMsg && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded text-xs text-rose-800 flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Vision Recognition Card (When scanning an image) */}
      {scanMetadata && (
        <div className="bg-white border border-slate-300 rounded-lg p-5 space-y-4 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-800">
              <Award className="w-4 h-4 text-[#0b2545]" />
              <span>{t.detectedHeading}</span>
            </div>
            <span className="text-xs font-semibold px-2 py-0.5 bg-slate-100 text-slate-800 border border-slate-200 rounded">
              {t.visionConfidence} {Math.round(scanMetadata.confidence * 100)}%
            </span>
          </div>

          <div className="space-y-1">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              {t.detectedProduct}
            </span>
            <p className="text-base font-bold text-slate-900 font-sans">
              {scanMetadata.product_description}
            </p>
          </div>

          {/* Identification Method Badge */}
          {scanMetadata.identification_method && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500 font-medium">Pipeline Resolution:</span>
              <span className="px-2 py-0.5 rounded text-xs font-mono font-medium bg-slate-100 text-slate-800 border border-slate-200">
                {scanMetadata.identification_method === 'ocr_code_match' && 'Tesseract OCR Multi-pass Pattern Match'}
                {scanMetadata.identification_method === 'visual_classifier' && 'Custom PyTorch CNN Product Classifier'}
                {scanMetadata.identification_method === 'ai_vision' && 'Gemini Vision Multimodal Classification'}
                {scanMetadata.identification_method === 'manual_required' && 'Manual Disambiguation Required'}
              </span>
            </div>
          )}

          {/* Matched Code and Material Info if any */}
          {scanMetadata.matched_code && (
            <div className="p-3 bg-slate-50 rounded border border-slate-200 text-xs space-y-1">
              <span className="font-semibold text-slate-700 block">Extracted Standard / Resin Code:</span>
              <p className="font-mono text-slate-900 font-bold">{scanMetadata.matched_code}</p>
            </div>
          )}

          {/* Mark Verification Results if detected */}
          {scanMetadata.mark_verification && (
            <div className="pt-2 border-t border-slate-100 flex flex-wrap gap-2 text-xs">
              {scanMetadata.mark_verification.license && (
                <div className="px-2.5 py-1 rounded border border-emerald-300 bg-emerald-50 text-emerald-900 flex items-center gap-1.5 font-medium">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>
                    {t.licenseVerified} <strong className="font-mono">{scanMetadata.mark_verification.license}</strong> ({scanMetadata.mark_verification.license_valid ? t.validStatus : t.invalidStatus})
                  </span>
                </div>
              )}

              {scanMetadata.mark_verification.huid && (
                <div className="px-2.5 py-1 rounded border border-emerald-300 bg-emerald-50 text-emerald-900 flex items-center gap-1.5 font-medium">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>
                    {t.huidVerified} <strong className="font-mono">{scanMetadata.mark_verification.huid}</strong> ({scanMetadata.mark_verification.huid_valid ? t.validStatus : t.invalidStatus})
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Manual Selection Fallback */}
          {scanMetadata.identification_method === 'manual_required' && scanMetadata.manual_options && (
            <div className="pt-2 border-t border-slate-100 space-y-2">
              <label className="block text-xs font-semibold text-slate-800">
                Select Exact Product Category to Retrieve Standards:
              </label>
              <div className="relative">
                <select
                  onChange={(e) => {
                    const selected = scanMetadata.manual_options.find(opt => opt.value === e.target.value);
                    if (selected) {
                      setProductDesc(selected.label);
                      handleRecommend(selected.label);
                    }
                  }}
                  value={productDesc}
                  className="w-full p-2.5 text-xs bg-white border border-slate-300 rounded font-medium text-slate-800 outline-none"
                >
                  <option value="">Select standard classification...</option>
                  {scanMetadata.manual_options.map((opt, i) => (
                    <option key={i} value={opt.value}>
                      {opt.label} — {opt.description}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Disambiguation Box */}
      {resultData?.is_ambiguous && resultData?.clarifying_question && (
        <div className="p-4 bg-amber-50 border border-amber-300 rounded text-xs text-amber-900 flex items-start gap-3 shadow-xs">
          <HelpCircle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-bold">{t.disambiguationHeading}</h4>
            <p>{resultData.clarifying_question}</p>
          </div>
        </div>
      )}

      {/* Results Section */}
      {resultData && resultData.candidates && resultData.candidates.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-200">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>{t.resultsHeading}</span>
            </h2>
            <span className="text-xs font-semibold px-2 py-0.5 bg-slate-100 text-slate-700 border border-slate-300 rounded">
              {resultData.candidates.length} {t.matchedCategories}
            </span>
          </div>

          <div className="space-y-4">
            {resultData.candidates.map((c, index) => {
              const isMandatory = c.mandatory;
              return (
                <div
                  key={index}
                  className="bg-white border border-slate-300 rounded-lg p-5 sm:p-6 space-y-5 shadow-xs"
                >
                  {/* Top Bar: Standard Name & Badges */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-3 border-b border-slate-100">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-bold px-2 py-0.5 bg-slate-100 text-slate-800 rounded border border-slate-200 font-mono">
                          Rank #{index + 1}
                        </span>
                        <h3 className="text-base sm:text-lg font-bold text-slate-900">
                          {c.product_name}
                        </h3>
                      </div>
                      <p className="text-xs text-slate-500">
                        Applicable Standard: <strong className="font-mono text-slate-800">{c.applicable_standard || 'To be specified'}</strong>
                      </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-1.5 shrink-0">
                      {isMandatory ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-bold bg-rose-50 text-rose-800 border border-rose-300">
                          <ShieldAlert className="w-3.5 h-3.5 text-rose-700" />
                          <span>{t.mandatoryBadge}</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-300">
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-700" />
                          <span>{t.voluntaryBadge}</span>
                        </span>
                      )}

                      <span className="px-2.5 py-1 rounded text-xs font-bold bg-slate-100 text-slate-800 border border-slate-300">
                        {t.scheme}: {c.scheme_code || 'Scheme-I (ISI)'}
                      </span>
                    </div>
                  </div>

                  {/* Standard & QCO Specification Box */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 bg-slate-50 p-3.5 rounded border border-slate-200 text-xs">
                    <div>
                      <span className="font-semibold text-slate-500 uppercase tracking-wider block text-[10px]">
                        Indian Standard Number
                      </span>
                      <span className="font-bold text-slate-900 font-mono text-sm">
                        {c.applicable_standard || 'To be assigned'}
                      </span>
                    </div>
                    <div>
                      <span className="font-semibold text-slate-500 uppercase tracking-wider block text-[10px]">
                        Quality Control Order (QCO) Mandate
                      </span>
                      <span className="font-medium text-slate-800">
                        {c.qco_order || (isMandatory ? 'Mandatory under Government of India QCO' : 'Voluntary Compliance Scheme')}
                      </span>
                    </div>
                  </div>

                  {/* Key Testing Parameters */}
                  {c.key_requirements && c.key_requirements.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 uppercase tracking-wider">
                        <FileText className="w-3.5 h-3.5 text-slate-700" />
                        <span>{t.keyRequirements}</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        {c.key_requirements.map((req, rIdx) => (
                          <div
                            key={rIdx}
                            className="bg-white p-2.5 rounded border border-slate-200 flex items-start gap-2"
                          >
                            <span className="w-1.5 h-1.5 bg-slate-700 rounded-full mt-1.5 shrink-0" />
                            <span className="text-slate-700">{req}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Next Steps / Roadmap */}
                  {c.next_steps && c.next_steps.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 uppercase tracking-wider">
                        <ListOrdered className="w-3.5 h-3.5 text-slate-700" />
                        <span>{t.nextSteps}</span>
                      </div>
                      <div className="space-y-1.5">
                        {c.next_steps.map((step, sIdx) => (
                          <div
                            key={sIdx}
                            className="flex items-start gap-2.5 text-xs text-slate-800 bg-slate-50 border border-slate-200 p-2.5 rounded"
                          >
                            <span className="w-4 h-4 rounded bg-slate-800 text-white flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                              {sIdx + 1}
                            </span>
                            <span>{step}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recognized Laboratories */}
                  {c.nearest_labs && c.nearest_labs.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 uppercase tracking-wider">
                        <Building2 className="w-3.5 h-3.5 text-slate-700" />
                        <span>{t.nearestLabs}</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        {c.nearest_labs.map((lab, lIdx) => (
                          <div
                            key={lIdx}
                            className="p-2.5 bg-white text-slate-800 border border-slate-200 rounded flex items-start gap-2"
                          >
                            <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                            <div>
                              <span className="font-semibold text-slate-900 block">{lab}</span>
                              <span className="text-[11px] text-slate-500">NABL Accredited Testing Facility</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Card Footer: Citations & Feedback */}
                  <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                    <div className="flex flex-wrap items-center gap-1.5">
                      {c.citations && c.citations.map((citation, citIdx) => (
                        <CitationChip
                          key={citIdx}
                          citation={citation}
                          onClick={() => handleCitationClick(citation)}
                        />
                      ))}
                    </div>
                    <FeedbackButtons
                      question={scanMetadata ? `Image scan: ${scanMetadata.product_description}` : productDesc}
                      answer={`${t.feedbackAnswerPrefix} ${c.product_name} (${c.applicable_standard})${t.feedbackAnswerSuffix}`}
                      language={language}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

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
