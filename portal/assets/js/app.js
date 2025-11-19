// SpeakSense Admin Portal - Vue.js Application

const { createApp } = Vue;

createApp({
    data() {
        return {
            // Language & i18n
            currentLanguage: localStorage.getItem('language') || 'zh',

            // Configuration
            config: {
                asrUrl: 'http://localhost:8001',
                retrievalUrl: 'http://localhost:8002',
                adminUrl: 'http://localhost:8003'
            },

            // UI State
            currentPage: 'dashboard',
            loading: false,
            showAddModal: false,
            showEditModal: false,
            searchQuery: '',

            // Data
            faqs: [],
            stats: {
                totalFAQs: 0,
                bm25Documents: 0,
                vectorDocuments: 0,
                categories: [],
                languages: []
            },
            dashboardStats: {
                today_queries: 0,
                total_queries: 0,
                avg_response_time: 0,
                top_faqs: [],
                intent_distribution: [],
                daily_trend: []
            },

            // Services Status
            services: {
                asr: false,
                retrieval: false,
                admin: false
            },

            // FAQ Form
            faqForm: {
                question: '',
                answer: '',
                alternative_questions: [],
                language: 'auto',
                category: 'general'
            },
            editingFAQId: null,
            previewingAudio: false,
            previewAudioUrl: null,
            audioKey: 0,
            previewCountdown: 0,
            previewCountdownTimer: null,

            // Notification
            notification: {
                show: false,
                message: '',
                type: 'info'
            },

            // Query Testing
            queryForm: {
                text: '',
                language: 'auto',
                method: 'hybrid'
            },
            queryResult: null,

            // ASR Testing
            asrForm: {
                audioFile: null,
                language: 'auto'
            },
            asrResult: null,

            // Recording
            recording: {
                isRecording: false,
                mediaRecorder: null,
                chunks: [],
                duration: 0,
                timer: null
            },

            // Intent Management
            intents: [],
            intentSearchQuery: '',
            showAddIntentModal: false,
            showEditIntentModal: false,
            intentForm: {
                intent_name: '',
                description: '',
                trigger_phrases: [],
                action_type: 'open_app',
                action_config: {},
                language: 'auto',
                category: 'general'
            },
            actionConfigJson: '{}',
            editingIntentId: null,

            // Query Logs
            queryLogs: [],
            logFilter: 'all',
            logOffset: 0,
            logLimit: 50
        };
    },

    computed: {
        filteredFAQs() {
            if (!this.searchQuery) return this.faqs;

            const query = this.searchQuery.toLowerCase();
            return this.faqs.filter(faq =>
                faq.question.toLowerCase().includes(query) ||
                faq.answer.toLowerCase().includes(query) ||
                faq.category.toLowerCase().includes(query)
            );
        },

        filteredIntents() {
            if (!this.intentSearchQuery) return this.intents;

            const query = this.intentSearchQuery.toLowerCase();
            return this.intents.filter(intent =>
                intent.intent_name.toLowerCase().includes(query) ||
                intent.description.toLowerCase().includes(query) ||
                intent.action_type.toLowerCase().includes(query) ||
                intent.category.toLowerCase().includes(query)
            );
        },

        translations() {
            return {
                zh: {
                    // App Title
                    appName: 'SpeakSense',
                    adminPortal: '管理后台',

                    // Navigation
                    dashboard: '仪表盘',
                    faqManagement: '常见问题管理',
                    intentManagement: '意图管理',
                    queryTesting: '查询测试',
                    queryLogs: '查询日志',
                    systemSettings: '系统设置',

                    // Services Status
                    services: '服务状态',
                    asrService: 'ASR服务',
                    retrieval: '检索服务',
                    admin: '管理服务',

                    // Dashboard
                    refresh: '刷新',
                    todayQueries: '今日查询',
                    totalQueries: '总查询数',
                    avgResponseTime: '平均响应时间',
                    topFAQs: '高频常见问题',
                    intentDistribution: '意图分布',
                    weeklyTrend: '7天趋势',
                    times: '次',
                    noQueryData: '暂无查询数据',
                    noQueryDataHint: '当用户开始使用查询功能后，这里将显示统计数据',

                    // Query Logs
                    allTypes: '全部类型',
                    faqOnly: '仅常见问题',
                    intentOnly: '仅意图',
                    noMatchOnly: '无匹配',
                    timestamp: '时间',
                    queryText: '查询内容',
                    matchType: '匹配类型',
                    matchedQuestion: '匹配结果',
                    responseTime: '响应时间',
                    noLogsFound: '暂无日志记录',
                    noLogsHint: '当用户发起查询后，这里将显示详细的查询记录',
                    previous: '上一页',
                    next: '下一页',
                    showing: '显示',
                    faqMatch: '常见问题',
                    intentMatch: '意图',
                    noMatch: '无匹配',

                    // FAQ Management
                    searchFAQs: '搜索常见问题...',
                    addNewFAQ: '添加新常见问题',
                    rebuildIndices: '重建索引',
                    question: '问题',
                    answer: '答案',
                    language: '语言',
                    category: '类别',
                    audio: '音频',
                    actions: '操作',
                    alternatives: '个替代问题',
                    noAudio: '无音频',
                    noFAQsFound: '未找到常见问题',
                    edit: '编辑',
                    delete: '删除',
                    editFAQ: '编辑常见问题',
                    previewAudio: '试听音频',
                    questionRequired: '问题 *',
                    questionPlaceholder: '输入主要问题',
                    answerRequired: '答案 *',
                    answerPlaceholder: '输入答案',
                    alternativeQuestions: '替代问题',
                    alternativeQuestionPlaceholder: '替代问题',
                    addAlternative: '+ 添加替代问题',
                    languageRequired: '语言 *',
                    categoryRequired: '类别 *',
                    categoryPlaceholder: '例如：营业时间、服务',
                    cancel: '取消',
                    update: '更新',
                    create: '创建',

                    // Intent Management
                    searchIntents: '搜索意图...',
                    intentName: '意图名称',
                    description: '描述',
                    triggerPhrases: '触发短语',
                    actionType: '动作类型',
                    more: '更多',
                    noIntentsFound: '未找到意图',
                    addNewIntent: '添加新意图',
                    editIntent: '编辑意图',
                    intent: '意图',
                    intentNameRequired: '意图名称 *',
                    intentNamePlaceholder: '例如：借书',
                    intentNameHint: '该意图的唯一标识符（使用下划线命名法）',
                    descriptionRequired: '描述 *',
                    descriptionPlaceholder: '这个意图是做什么的？',
                    triggerPhrasesRequired: '触发短语 *',
                    triggerPhrasePlaceholder: '例如：我想借一本书',
                    addTriggerPhrase: '+ 添加触发短语',
                    actionTypeRequired: '动作类型 *',
                    openApp: '打开应用',
                    apiCall: 'API调用',
                    navigate: '导航',
                    executeFunction: '执行函数',
                    custom: '自定义',
                    actionConfigRequired: '动作配置 (JSON) *',
                    actionConfigPlaceholder: '{"app_id": "book_borrowing_app", "params": {}}',
                    actionConfigHint: '输入有效的JSON作为动作配置',
                    categoryPlaceholderIntent: '例如：导航、服务',

                    // Query Testing
                    testTextQuery: '测试文本查询',
                    enterYourQuestion: '输入您的问题',
                    searchMethod: '搜索方式',
                    autoDetect: '自动检测',
                    chinese: '中文',
                    english: '英语',
                    hybrid: '混合 (BM25 + 向量)',
                    bm25Only: '仅BM25',
                    vectorOnly: '仅向量',
                    search: '搜索',
                    extractedParameters: '提取的参数',
                    intentMatched: '意图匹配成功',
                    confidence: '置信度',
                    matchedPhrase: '匹配短语',
                    actionConfiguration: '动作配置',
                    faqMatchFound: '常见问题匹配成功',
                    matchedBy: '匹配方式',
                    audioResponse: '音频回复',
                    noAudioAvailable: '无音频',
                    audioPending: '等待生成',
                    audioGenerating: '生成中...',
                    audioFailed: '生成失败',
                    refreshStatus: '刷新状态',
                    matchFound: '匹配成功',
                    noMatchFound: '未找到匹配',
                    testAudioQuery: '测试音频查询 (ASR)',
                    recordWithMicrophone: '使用麦克风录音',
                    startRecording: '开始录音',
                    stopRecording: '停止录音',
                    recording: '录音中...',
                    microphoneNote: '注意：麦克风访问需要HTTPS或localhost',
                    or: '或',
                    uploadAudioFile: '上传音频文件',
                    transcribeAndSearch: '转录并搜索',

                    // Results
                    intentMatched: '匹配到意图',
                    faqMatchFound: '找到常见问题匹配',
                    matchFound: '找到匹配',
                    noMatchFound: '未找到匹配',
                    confidence: '置信度',
                    matchedPhrase: '匹配短语',
                    actionConfiguration: '动作配置',
                    matchedBy: '匹配方式',
                    audioResponse: '音频回复',
                    transcriptionResult: '转录结果',
                    recognizedText: '识别文本',

                    // Modal - FAQ
                    addFAQ: '添加常见问题',
                    editFAQ: '编辑常见问题',
                    questionRequired: '问题 *',
                    answerRequired: '答案 *',
                    alternativeQuestions: '替代问题',
                    addAlternative: '+ 添加替代问题',
                    languageRequired: '语言 *',
                    categoryRequired: '类别 *',
                    cancel: '取消',
                    create: '创建',
                    update: '更新',

                    // Modal - Intent
                    addIntent: '添加意图',
                    editIntent: '编辑意图',
                    intentNameRequired: '意图名称 *',
                    intentNamePlaceholder: '例如：borrow_book',
                    intentNameHint: '意图的唯一标识符（使用下划线命名）',
                    descriptionRequired: '描述 *',
                    descriptionPlaceholder: '这个意图是做什么的？',
                    triggerPhrasesRequired: '触发短语 *',
                    triggerPhrasePlaceholder: '例如：我想借一本书',
                    addTriggerPhrase: '+ 添加触发短语',
                    actionTypeRequired: '动作类型 *',
                    openApp: '打开应用',
                    apiCall: 'API调用',
                    navigate: '导航',
                    executeFunction: '执行函数',
                    custom: '自定义',
                    actionConfigRequired: '动作配置 (JSON) *',
                    actionConfigPlaceholder: '{"app_id": "book_borrowing_app", "params": {}}',
                    actionConfigHint: '输入有效的JSON作为动作配置',

                    // Settings
                    serviceConfiguration: '服务配置',
                    asrServiceURL: 'ASR服务URL',
                    retrievalServiceURL: '检索服务URL',
                    adminServiceURL: '管理服务URL',
                    languagePreference: '语言偏好',
                    languagePreferenceDesc: '选择管理界面的显示语言',
                    systemInformation: '系统信息',
                    version: '版本',
                    ttsEngine: 'TTS引擎',
                    embeddingModel: '嵌入模型',
                    asrModel: 'ASR模型',
                    audioManagement: '音频管理',
                    audioManagementDesc: '重新生成所有常见问题的音频文件。当切换TTS模型或修复音频问题时使用。',
                    regenerateAllAudio: '重新生成所有音频',
                    testingPortal: '测试门户',
                    testingPortalDesc: '访问开发测试门户进行高级调试和测试',
                    openTestingPortal: '打开测试门户 →',

                    // Notifications
                    statisticsRefreshed: '统计数据已刷新',
                    failedToRefreshStats: '刷新统计数据失败',
                    failedToLoadFAQs: '加载常见问题失败',
                    questionIsRequired: '问题为必填项',
                    answerIsRequired: '答案为必填项',
                    faqUpdatedSuccessfully: '常见问题更新成功',
                    faqCreatedSuccessfully: '常见问题创建成功',
                    failedToSaveFAQ: '保存常见问题失败',
                    faqDeletedSuccessfully: '常见问题删除成功',
                    failedToDeleteFAQ: '删除常见问题失败',
                    audioPreviewFailed: '音频试听失败',
                    intentUpdatedSuccessfully: '意图更新成功',
                    intentCreatedSuccessfully: '意图创建成功',
                    failedToSaveIntent: '保存意图失败',
                    intentDeletedSuccessfully: '意图删除成功',
                    failedToDeleteIntent: '删除意图失败',
                    intentNameIsRequired: '意图名称为必填项',
                    descriptionIsRequired: '描述为必填项',
                    atLeastOneTriggerPhrase: '至少需要一个触发短语',
                    invalidJSON: '动作配置中的JSON无效',
                    pleaseEnterQuestion: '请输入问题',
                    matchFoundNotif: '找到匹配！',
                    noMatchFoundNotif: '未找到匹配',
                    queryFailed: '查询失败',
                    pleaseSelectAudioFile: '请选择音频文件',
                    audioTranscribedSuccessfully: '音频转录成功',
                    asrTranscriptionFailed: 'ASR转录失败',
                    recordingStarted: '录音已开始',
                    recordingStopped: '录音已停止。准备转录！',
                    noAudioData: '未录制音频数据。请重试。',
                    recordingIsEmpty: '录音为空。请重试。',
                    errorAccessingMicrophone: '访问麦克风时出错',
                    makeSureHTTPS: '。确保使用HTTPS或localhost。',
                    loading: '加载中...'
                },
                en: {
                    // App Title
                    appName: 'SpeakSense',
                    adminPortal: 'Admin Portal',

                    // Navigation
                    dashboard: 'Dashboard',
                    faqManagement: 'FAQ Management',
                    intentManagement: 'Intent Management',
                    queryTesting: 'Query Testing',
                    queryLogs: 'Query Logs',
                    systemSettings: 'System Settings',

                    // Services Status
                    services: 'Services',
                    asrService: 'ASR Service',
                    retrieval: 'Retrieval',
                    admin: 'Admin',

                    // Dashboard
                    refresh: 'Refresh',
                    todayQueries: 'Today Queries',
                    totalQueries: 'Total Queries',
                    avgResponseTime: 'Avg Response Time',
                    topFAQs: 'Top FAQs',
                    intentDistribution: 'Intent Distribution',
                    weeklyTrend: '7-Day Trend',
                    times: 'times',
                    noQueryData: 'No Query Data',
                    noQueryDataHint: 'Statistics will appear here once users start querying',

                    // Query Logs
                    allTypes: 'All Types',
                    faqOnly: 'FAQ Only',
                    intentOnly: 'Intent Only',
                    noMatchOnly: 'No Match Only',
                    timestamp: 'Timestamp',
                    queryText: 'Query Text',
                    matchType: 'Match Type',
                    matchedQuestion: 'Matched Result',
                    responseTime: 'Response Time',
                    noLogsFound: 'No Logs Found',
                    noLogsHint: 'Query logs will appear here once users start querying',
                    previous: 'Previous',
                    next: 'Next',
                    showing: 'Showing',
                    faqMatch: 'FAQ',
                    intentMatch: 'Intent',
                    noMatch: 'No Match',

                    // FAQ Management
                    searchFAQs: 'Search FAQs...',
                    addNewFAQ: 'Add New FAQ',
                    rebuildIndices: 'Rebuild Indices',
                    question: 'Question',
                    answer: 'Answer',
                    language: 'Language',
                    category: 'Category',
                    audio: 'Audio',
                    actions: 'Actions',
                    alternatives: ' alternatives',
                    noAudio: 'No audio',
                    noFAQsFound: 'No FAQs found',
                    edit: 'Edit',
                    delete: 'Delete',
                    editFAQ: 'Edit FAQ',
                    previewAudio: 'Preview Audio',
                    questionRequired: 'Question *',
                    questionPlaceholder: 'Enter the main question',
                    answerRequired: 'Answer *',
                    answerPlaceholder: 'Enter the answer',
                    alternativeQuestions: 'Alternative Questions',
                    alternativeQuestionPlaceholder: 'Alternative question',
                    addAlternative: '+ Add Alternative',
                    languageRequired: 'Language *',
                    categoryRequired: 'Category *',
                    categoryPlaceholder: 'e.g., hours, services',
                    cancel: 'Cancel',
                    update: 'Update',
                    create: 'Create',

                    // Intent Management
                    searchIntents: 'Search intents...',
                    intentName: 'Intent Name',
                    description: 'Description',
                    triggerPhrases: 'Trigger Phrases',
                    actionType: 'Action Type',
                    more: ' more',
                    noIntentsFound: 'No intents found',
                    addNewIntent: 'Add New Intent',
                    editIntent: 'Edit Intent',
                    intent: 'Intent',
                    intentNameRequired: 'Intent Name *',
                    intentNamePlaceholder: 'e.g., borrow_book',
                    intentNameHint: 'Unique identifier for this intent (use snake_case)',
                    descriptionRequired: 'Description *',
                    descriptionPlaceholder: 'What does this intent do?',
                    triggerPhrasesRequired: 'Trigger Phrases *',
                    triggerPhrasePlaceholder: 'e.g., I would like to borrow a book',
                    addTriggerPhrase: '+ Add Trigger Phrase',
                    actionTypeRequired: 'Action Type *',
                    openApp: 'Open App',
                    apiCall: 'API Call',
                    navigate: 'Navigate',
                    executeFunction: 'Execute Function',
                    custom: 'Custom',
                    actionConfigRequired: 'Action Configuration (JSON) *',
                    actionConfigPlaceholder: '{"app_id": "book_borrowing_app", "params": {}}',
                    actionConfigHint: 'Enter valid JSON for action configuration',
                    categoryPlaceholderIntent: 'e.g., navigation, services',

                    // Query Testing
                    testTextQuery: 'Test Text Query',
                    enterYourQuestion: 'Enter Your Question',
                    searchMethod: 'Search Method',
                    autoDetect: 'Auto Detect',
                    chinese: 'Chinese',
                    english: 'English',
                    hybrid: 'Hybrid (BM25 + Vector)',
                    bm25Only: 'BM25 Only',
                    vectorOnly: 'Vector Only',
                    search: 'Search',
                    extractedParameters: 'Extracted Parameters',
                    intentMatched: 'Intent Matched',
                    confidence: 'confidence',
                    matchedPhrase: 'Matched Phrase',
                    actionConfiguration: 'Action Configuration',
                    faqMatchFound: 'FAQ Match Found',
                    matchedBy: 'Matched By',
                    audioResponse: 'Audio Response',
                    noAudioAvailable: 'No audio available',
                    audioPending: 'Pending',
                    audioGenerating: 'Generating...',
                    audioFailed: 'Failed',
                    refreshStatus: 'Refresh',
                    matchFound: 'Match Found',
                    noMatchFound: 'No Match Found',
                    testAudioQuery: 'Test Audio Query (ASR)',
                    recordWithMicrophone: 'Record with Microphone',
                    startRecording: 'Start Recording',
                    stopRecording: 'Stop Recording',
                    recording: 'Recording...',
                    microphoneNote: 'Note: Microphone access requires HTTPS or localhost',
                    or: 'OR',
                    uploadAudioFile: 'Upload Audio File',
                    transcribeAndSearch: 'Transcribe & Search',

                    // Results
                    intentMatched: 'Intent Matched',
                    faqMatchFound: 'FAQ Match Found',
                    matchFound: 'Match Found',
                    noMatchFound: 'No Match Found',
                    confidence: 'confidence',
                    matchedPhrase: 'Matched Phrase',
                    actionConfiguration: 'Action Configuration',
                    matchedBy: 'Matched By',
                    audioResponse: 'Audio Response',
                    transcriptionResult: 'Transcription Result',
                    recognizedText: 'Recognized Text',

                    // Modal - FAQ
                    addFAQ: 'Add New FAQ',
                    editFAQ: 'Edit FAQ',
                    questionRequired: 'Question *',
                    answerRequired: 'Answer *',
                    alternativeQuestions: 'Alternative Questions',
                    addAlternative: '+ Add Alternative',
                    languageRequired: 'Language *',
                    categoryRequired: 'Category *',
                    cancel: 'Cancel',
                    create: 'Create',
                    update: 'Update',

                    // Modal - Intent
                    addIntent: 'Add New Intent',
                    editIntent: 'Edit Intent',
                    intentNameRequired: 'Intent Name *',
                    intentNamePlaceholder: 'e.g., borrow_book',
                    intentNameHint: 'Unique identifier for this intent (use snake_case)',
                    descriptionRequired: 'Description *',
                    descriptionPlaceholder: 'What does this intent do?',
                    triggerPhrasesRequired: 'Trigger Phrases *',
                    triggerPhrasePlaceholder: 'e.g., I would like to borrow a book',
                    addTriggerPhrase: '+ Add Trigger Phrase',
                    actionTypeRequired: 'Action Type *',
                    openApp: 'Open App',
                    apiCall: 'API Call',
                    navigate: 'Navigate',
                    executeFunction: 'Execute Function',
                    custom: 'Custom',
                    actionConfigRequired: 'Action Configuration (JSON) *',
                    actionConfigPlaceholder: '{"app_id": "book_borrowing_app", "params": {}}',
                    actionConfigHint: 'Enter valid JSON for action configuration',

                    // Settings
                    serviceConfiguration: 'Service Configuration',
                    asrServiceURL: 'ASR Service URL',
                    retrievalServiceURL: 'Retrieval Service URL',
                    adminServiceURL: 'Admin Service URL',
                    languagePreference: 'Language Preference',
                    languagePreferenceDesc: 'Choose the display language for the admin interface',
                    systemInformation: 'System Information',
                    version: 'Version',
                    ttsEngine: 'TTS Engine',
                    embeddingModel: 'Embedding Model',
                    asrModel: 'ASR Model',
                    audioManagement: 'Audio Management',
                    audioManagementDesc: 'Regenerate audio files for all FAQs. Use when switching TTS models or fixing audio issues.',
                    regenerateAllAudio: 'Regenerate All Audio',
                    testingPortal: 'Testing Portal',
                    testingPortalDesc: 'Access the development testing portal for advanced debugging and testing.',
                    openTestingPortal: 'Open Testing Portal →',

                    // Notifications
                    statisticsRefreshed: 'Statistics refreshed',
                    failedToRefreshStats: 'Failed to refresh statistics',
                    failedToLoadFAQs: 'Failed to load FAQs',
                    questionIsRequired: 'Question is required',
                    answerIsRequired: 'Answer is required',
                    faqUpdatedSuccessfully: 'FAQ updated successfully',
                    faqCreatedSuccessfully: 'FAQ created successfully',
                    failedToSaveFAQ: 'Failed to save FAQ',
                    faqDeletedSuccessfully: 'FAQ deleted successfully',
                    failedToDeleteFAQ: 'Failed to delete FAQ',
                    audioPreviewFailed: 'Audio preview failed',
                    intentUpdatedSuccessfully: 'Intent updated successfully',
                    intentCreatedSuccessfully: 'Intent created successfully',
                    failedToSaveIntent: 'Failed to save intent',
                    intentDeletedSuccessfully: 'Intent deleted successfully',
                    failedToDeleteIntent: 'Failed to delete intent',
                    intentNameIsRequired: 'Intent name is required',
                    descriptionIsRequired: 'Description is required',
                    atLeastOneTriggerPhrase: 'At least one trigger phrase is required',
                    invalidJSON: 'Invalid JSON in action configuration',
                    pleaseEnterQuestion: 'Please enter a question',
                    matchFoundNotif: 'Match found!',
                    noMatchFoundNotif: 'No match found',
                    queryFailed: 'Query failed',
                    pleaseSelectAudioFile: 'Please select an audio file',
                    audioTranscribedSuccessfully: 'Audio transcribed successfully',
                    asrTranscriptionFailed: 'ASR transcription failed',
                    recordingStarted: 'Recording started',
                    recordingStopped: 'Recording stopped. Ready to transcribe!',
                    noAudioData: 'No audio data recorded. Please try again.',
                    recordingIsEmpty: 'Recording is empty. Please try again.',
                    errorAccessingMicrophone: 'Error accessing microphone',
                    makeSureHTTPS: '. Make sure you are using HTTPS or localhost.',
                    loading: 'Loading...'
                }
            };
        }
    },

    methods: {
        // ========================================
        // Internationalization
        // ========================================
        t(key) {
            const lang = this.translations[this.currentLanguage];
            return lang && lang[key] ? lang[key] : key;
        },

        changeLanguage(lang) {
            this.currentLanguage = lang;
            localStorage.setItem('language', lang);
            this.showNotification(
                lang === 'zh' ? '语言已切换到简体中文' : 'Language switched to English',
                'success'
            );
        },
        // ========================================
        // Initialization
        // ========================================
        async init() {
            await this.checkServices();
            await this.refreshStats();
            await this.refreshDashboard();
            await this.loadFAQs();
            await this.loadIntents();
        },

        // ========================================
        // Service Health Checks
        // ========================================
        async checkServices() {
            try {
                const checks = await Promise.allSettled([
                    axios.get(`${this.config.asrUrl}/health`),
                    axios.get(`${this.config.retrievalUrl}/health`),
                    axios.get(`${this.config.adminUrl}/health`)
                ]);

                this.services.asr = checks[0].status === 'fulfilled';
                this.services.retrieval = checks[1].status === 'fulfilled';
                this.services.admin = checks[2].status === 'fulfilled';
            } catch (error) {
                console.error('Service health check failed:', error);
            }
        },

        // ========================================
        // Dashboard Statistics
        // ========================================
        async refreshStats() {
            try {
                this.loading = true;

                // Get FAQ stats
                const adminStats = await axios.get(`${this.config.adminUrl}/admin/stats`);
                const retrievalStats = await axios.get(`${this.config.retrievalUrl}/retrieval/stats`);

                this.stats = {
                    totalFAQs: adminStats.data.total_faqs || 0,
                    bm25Documents: retrievalStats.data.bm25_documents || 0,
                    vectorDocuments: retrievalStats.data.vector_documents || 0,
                    categories: adminStats.data.categories || [],
                    languages: adminStats.data.languages || []
                };

                this.showNotification('Statistics refreshed', 'success');
            } catch (error) {
                console.error('Failed to refresh stats:', error);
                this.showNotification('Failed to refresh statistics', 'error');
            } finally {
                this.loading = false;
            }
        },

        async refreshDashboard() {
            try {
                this.loading = true;

                // Get dashboard analytics
                const response = await axios.get(`${this.config.adminUrl}/admin/stats/dashboard`);

                this.dashboardStats = {
                    today_queries: response.data.today_queries || 0,
                    total_queries: response.data.total_queries || 0,
                    avg_response_time: response.data.avg_response_time || 0,
                    top_faqs: response.data.top_faqs || [],
                    intent_distribution: response.data.intent_distribution || [],
                    daily_trend: response.data.daily_trend || []
                };

                this.showNotification('Dashboard refreshed', 'success');
            } catch (error) {
                console.error('Failed to refresh dashboard:', error);
                this.showNotification('Failed to refresh dashboard', 'error');
            } finally {
                this.loading = false;
            }
        },

        getTrendHeight(count) {
            // Calculate height percentage for trend chart
            if (!this.dashboardStats.daily_trend || this.dashboardStats.daily_trend.length === 0) {
                return 0;
            }

            const maxCount = Math.max(...this.dashboardStats.daily_trend.map(d => d.count));
            if (maxCount === 0) return 0;

            return Math.max((count / maxCount) * 100, 5); // Minimum 5% height for visibility
        },

        formatDate(dateStr) {
            // Format date string (YYYY-MM-DD) to MM/DD
            if (!dateStr) return '';
            const parts = dateStr.split('-');
            return parts.length === 3 ? `${parts[1]}/${parts[2]}` : dateStr;
        },

        getPieColor(index) {
            // Color palette for pie chart segments
            const colors = [
                '#4169E1',  // Royal Blue
                '#00B4D8',  // Cyan
                '#00C48C',  // Green
                '#FFA502',  // Orange
                '#FF6B9D',  // Pink
                '#9B59B6',  // Purple
                '#3498DB',  // Light Blue
                '#E74C3C'   // Red
            ];
            return colors[index % colors.length];
        },

        getIntentPercentage(count) {
            // Calculate percentage of total for this intent
            if (!this.dashboardStats.intent_distribution || this.dashboardStats.intent_distribution.length === 0) {
                return 0;
            }

            const total = this.dashboardStats.intent_distribution.reduce((sum, intent) => sum + intent.count, 0);
            if (total === 0) return 0;

            return ((count / total) * 100).toFixed(1);
        },

        getPieChartGradient() {
            // Generate conic-gradient CSS for pie chart
            if (!this.dashboardStats.intent_distribution || this.dashboardStats.intent_distribution.length === 0) {
                return 'conic-gradient(#E5E7EB 0deg 360deg)';
            }

            const total = this.dashboardStats.intent_distribution.reduce((sum, intent) => sum + intent.count, 0);
            if (total === 0) {
                return 'conic-gradient(#E5E7EB 0deg 360deg)';
            }

            let currentDeg = 0;
            const segments = this.dashboardStats.intent_distribution.map((intent, index) => {
                const percentage = (intent.count / total) * 100;
                const degrees = (percentage / 100) * 360;
                const color = this.getPieColor(index);
                const startDeg = currentDeg;
                const endDeg = currentDeg + degrees;
                currentDeg = endDeg;

                return `${color} ${startDeg}deg ${endDeg}deg`;
            });

            return `conic-gradient(${segments.join(', ')})`;
        },

        // ========================================
        // FAQ Management
        // ========================================
        async loadFAQs() {
            try {
                const response = await axios.get(`${this.config.adminUrl}/admin/faqs`);
                this.faqs = response.data;
            } catch (error) {
                console.error('Failed to load FAQs:', error);
                this.showNotification('Failed to load FAQs', 'error');
            }
        },

        async refreshFAQ(answerId) {
            // Refresh a single FAQ to check audio generation status
            await this.loadFAQs();
            this.showNotification('Status refreshed', 'success');
        },

        async saveFAQ() {
            // Validation
            if (!this.faqForm.question.trim()) {
                this.showNotification('Question is required', 'error');
                return;
            }
            if (!this.faqForm.answer.trim()) {
                this.showNotification('Answer is required', 'error');
                return;
            }

            try {
                this.loading = true;

                // Filter out empty alternative questions
                const altQuestions = this.faqForm.alternative_questions
                    .filter(q => q.trim() !== '');

                const payload = {
                    question: this.faqForm.question,
                    answer: this.faqForm.answer,
                    alternative_questions: altQuestions,
                    language: this.faqForm.language,
                    category: this.faqForm.category
                };

                if (this.showEditModal && this.editingFAQId) {
                    // Update existing FAQ
                    await axios.put(
                        `${this.config.adminUrl}/admin/faq/${this.editingFAQId}`,
                        payload
                    );
                    this.showNotification('FAQ updated successfully', 'success');
                } else {
                    // Create new FAQ
                    await axios.post(`${this.config.adminUrl}/admin/faq`, payload);
                    this.showNotification('FAQ created successfully', 'success');
                }

                await this.loadFAQs();
                await this.refreshStats();
                this.closeModal();
            } catch (error) {
                console.error('Failed to save FAQ:', error);
                this.showNotification(
                    error.response?.data?.detail || 'Failed to save FAQ',
                    'error'
                );
            } finally {
                this.loading = false;
            }
        },

        editFAQ(faq) {
            this.faqForm = {
                question: faq.question,
                answer: faq.answer,
                alternative_questions: [...faq.alternative_questions],
                language: faq.language,
                category: faq.category
            };
            this.editingFAQId = faq.answer_id;
            this.showEditModal = true;
        },

        async deleteFAQ(faq) {
            if (!confirm(`Are you sure you want to delete the FAQ: "${faq.question}"?`)) {
                return;
            }

            try {
                this.loading = true;
                await axios.delete(`${this.config.adminUrl}/admin/faq/${faq.answer_id}`);
                this.showNotification('FAQ deleted successfully', 'success');
                await this.loadFAQs();
                await this.refreshStats();
            } catch (error) {
                console.error('Failed to delete FAQ:', error);
                this.showNotification('Failed to delete FAQ', 'error');
            } finally {
                this.loading = false;
            }
        },

        addAltQuestion() {
            this.faqForm.alternative_questions.push('');
        },

        removeAltQuestion(index) {
            this.faqForm.alternative_questions.splice(index, 1);
        },

        closeModal() {
            this.showAddModal = false;
            this.showEditModal = false;
            this.editingFAQId = null;
            this.previewAudioUrl = null;
            this.faqForm = {
                question: '',
                answer: '',
                alternative_questions: [],
                language: 'auto',
                category: 'general'
            };
        },

        async previewAudio() {
            if (!this.faqForm.answer) {
                this.showNotification(this.t('answerIsRequired'), 'warning');
                return;
            }

            try {
                this.previewingAudio = true;
                this.previewCountdown = 60;  // Start at 60 seconds (1 minute)

                // Start countdown timer
                this.previewCountdownTimer = setInterval(() => {
                    if (this.previewCountdown > 0) {
                        this.previewCountdown--;
                    }
                }, 1000);

                // Create FormData for the preview request
                const formData = new FormData();
                formData.append('text', this.faqForm.answer);
                formData.append('language', this.faqForm.language);

                // Debug: Log what we're sending
                console.log('[Preview Audio] Sending text:', this.faqForm.answer);
                console.log('[Preview Audio] Text length:', this.faqForm.answer.length);

                // Get audio preview (add timestamp to prevent caching)
                const response = await axios.post(
                    `${this.config.adminUrl}/admin/preview_audio?t=${Date.now()}`,
                    formData,
                    {
                        responseType: 'blob',
                        headers: {
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache'
                        }
                    }
                );

                // Debug: Log what we received
                console.log('[Preview Audio] Received blob size:', response.data.size, 'bytes');

                // Create blob from response
                const audioBlob = new Blob([response.data], { type: 'audio/wav' });

                // Revoke old URL if exists (if we were using blob URLs before)
                if (this.previewAudioUrl && this.previewAudioUrl.startsWith('blob:')) {
                    URL.revokeObjectURL(this.previewAudioUrl.split('#')[0]);
                }

                // First set to null to force destroy old audio element
                this.previewAudioUrl = null;
                this.audioKey++;  // Change key immediately to force Vue to destroy old element

                // Convert blob to data URL instead of blob URL to avoid Chrome caching
                const reader = new FileReader();
                reader.onloadend = () => {
                    // Use setTimeout instead of nextTick to give browser time to truly destroy old element
                    setTimeout(() => {
                        // Use data URL instead of blob URL
                        this.previewAudioUrl = reader.result;

                        console.log('[Preview Audio] Data URL length:', reader.result.length);

                        // Wait for audio element to be created, then play
                        this.$nextTick(() => {
                            const audioElement = document.getElementById('preview-audio-player');
                            if (audioElement) {
                                // Listen for when audio is actually loaded
                                audioElement.addEventListener('loadedmetadata', function() {
                                    console.log('[Preview Audio] Audio loaded! Duration:', this.duration, 'seconds');
                                }, { once: true });

                                audioElement.addEventListener('canplay', function() {
                                    console.log('[Preview Audio] Audio ready to play');
                                }, { once: true });

                                // Force stop any previous playback
                                audioElement.pause();
                                audioElement.currentTime = 0;

                                audioElement.load();
                                audioElement.play().then(() => {
                                    console.log('[Preview Audio] Playing started');
                                }).catch(err => {
                                    console.error('[Preview Audio] Play failed:', err);
                                });
                            }
                        });
                    }, 100);  // Wait 100ms for old element to be truly destroyed
                };

                // Start reading the blob as data URL
                reader.readAsDataURL(audioBlob);

            } catch (error) {
                console.error('Failed to preview audio:', error);
                this.showNotification(this.t('audioPreviewFailed'), 'error');
            } finally {
                // Clear countdown timer
                if (this.previewCountdownTimer) {
                    clearInterval(this.previewCountdownTimer);
                    this.previewCountdownTimer = null;
                }
                this.previewingAudio = false;
                this.previewCountdown = 0;
            }
        },

        // ========================================
        // System Actions
        // ========================================
        async rebuildIndices() {
            if (!confirm('This will rebuild the search indices. Continue?')) {
                return;
            }

            try {
                this.loading = true;
                const response = await axios.post(
                    `${this.config.retrievalUrl}/retrieval/rebuild_indices`
                );

                this.showNotification(
                    `Indices rebuilt: ${response.data.bm25_documents} BM25, ${response.data.vector_documents} Vector`,
                    'success'
                );
                await this.refreshStats();
            } catch (error) {
                console.error('Failed to rebuild indices:', error);
                this.showNotification('Failed to rebuild indices', 'error');
            } finally {
                this.loading = false;
            }
        },

        async regenerateAllAudio() {
            if (!confirm('This will regenerate audio files for all FAQs. This may take a while. Continue?')) {
                return;
            }

            try {
                this.loading = true;
                const response = await axios.post(
                    `${this.config.adminUrl}/admin/regenerate_all_audio`
                );

                const { total, success, failed } = response.data;
                this.showNotification(
                    `Audio regeneration complete: ${success}/${total} successful, ${failed} failed`,
                    failed > 0 ? 'warning' : 'success'
                );
            } catch (error) {
                console.error('Failed to regenerate audio:', error);
                this.showNotification('Failed to regenerate audio', 'error');
            } finally {
                this.loading = false;
            }
        },

        // ========================================
        // Intent Management
        // ========================================
        async loadIntents() {
            try {
                const response = await axios.get(`${this.config.adminUrl}/admin/intents`);
                this.intents = response.data;
            } catch (error) {
                console.error('Failed to load intents:', error);
                this.showNotification('Failed to load intents', 'error');
            }
        },

        async saveIntent() {
            // Validation
            if (!this.intentForm.intent_name.trim()) {
                this.showNotification('Intent name is required', 'error');
                return;
            }
            if (!this.intentForm.description.trim()) {
                this.showNotification('Description is required', 'error');
                return;
            }
            if (this.intentForm.trigger_phrases.length === 0) {
                this.showNotification('At least one trigger phrase is required', 'error');
                return;
            }

            // Parse action config JSON
            let actionConfig;
            try {
                actionConfig = JSON.parse(this.actionConfigJson);
            } catch (e) {
                this.showNotification('Invalid JSON in action configuration', 'error');
                return;
            }

            try {
                this.loading = true;

                // Filter out empty trigger phrases
                const triggerPhrases = this.intentForm.trigger_phrases
                    .filter(p => p.trim() !== '');

                const payload = {
                    intent_name: this.intentForm.intent_name,
                    description: this.intentForm.description,
                    trigger_phrases: triggerPhrases,
                    action_type: this.intentForm.action_type,
                    action_config: actionConfig,
                    language: this.intentForm.language,
                    category: this.intentForm.category
                };

                if (this.showEditIntentModal && this.editingIntentId) {
                    // Update existing intent
                    await axios.put(
                        `${this.config.adminUrl}/admin/intent/${this.editingIntentId}`,
                        payload
                    );
                    this.showNotification('Intent updated successfully', 'success');
                } else {
                    // Create new intent
                    await axios.post(`${this.config.adminUrl}/admin/intent`, payload);
                    this.showNotification('Intent created successfully', 'success');
                }

                await this.loadIntents();
                await this.refreshStats();
                this.closeIntentModal();
            } catch (error) {
                console.error('Failed to save intent:', error);
                this.showNotification(
                    error.response?.data?.detail || 'Failed to save intent',
                    'error'
                );
            } finally {
                this.loading = false;
            }
        },

        editIntent(intent) {
            this.intentForm = {
                intent_name: intent.intent_name,
                description: intent.description,
                trigger_phrases: [...intent.trigger_phrases],
                action_type: intent.action_type,
                action_config: intent.action_config,
                language: intent.language,
                category: intent.category
            };
            this.actionConfigJson = JSON.stringify(intent.action_config, null, 2);
            this.editingIntentId = intent.intent_id;
            this.showEditIntentModal = true;
        },

        async deleteIntent(intent) {
            if (!confirm(`Are you sure you want to delete the intent: "${intent.intent_name}"?`)) {
                return;
            }

            try {
                this.loading = true;
                await axios.delete(`${this.config.adminUrl}/admin/intent/${intent.intent_id}`);
                this.showNotification('Intent deleted successfully', 'success');
                await this.loadIntents();
                await this.refreshStats();
            } catch (error) {
                console.error('Failed to delete intent:', error);
                this.showNotification('Failed to delete intent', 'error');
            } finally {
                this.loading = false;
            }
        },

        addTriggerPhrase() {
            this.intentForm.trigger_phrases.push('');
        },

        removeTriggerPhrase(index) {
            this.intentForm.trigger_phrases.splice(index, 1);
        },

        closeIntentModal() {
            this.showAddIntentModal = false;
            this.showEditIntentModal = false;
            this.editingIntentId = null;
            this.intentForm = {
                intent_name: '',
                description: '',
                trigger_phrases: [],
                action_type: 'open_app',
                action_config: {},
                language: 'auto',
                category: 'general'
            };
            this.actionConfigJson = '{}';
        },

        // ========================================
        // Query Logs Management
        // ========================================
        async loadQueryLogs() {
            try {
                this.loading = true;
                const matchedType = this.logFilter === 'all' ? null : this.logFilter;

                const response = await axios.get(`${this.config.adminUrl}/admin/query_logs`, {
                    params: {
                        limit: this.logLimit,
                        offset: this.logOffset,
                        matched_type: matchedType
                    }
                });

                this.queryLogs = response.data;
            } catch (error) {
                console.error('Failed to load query logs:', error);
                this.showNotification('Failed to load query logs', 'error');
            } finally {
                this.loading = false;
            }
        },

        loadNextLogs() {
            this.logOffset += this.logLimit;
            this.loadQueryLogs();
        },

        loadPreviousLogs() {
            this.logOffset = Math.max(0, this.logOffset - this.logLimit);
            this.loadQueryLogs();
        },

        formatTimestamp(timestamp) {
            if (!timestamp) return '-';
            const date = new Date(timestamp);
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const seconds = String(date.getSeconds()).padStart(2, '0');
            return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        },

        getMatchTypeLabel(matchType) {
            const labels = {
                'faq': this.t('faqMatch'),
                'intent': this.t('intentMatch'),
                'none': this.t('noMatch')
            };
            return labels[matchType] || matchType || '-';
        },

        getMatchTypeBadgeStyle(matchType) {
            const styles = {
                'faq': {
                    background: 'rgba(0, 196, 140, 0.1)',
                    color: '#00C48C',
                    borderColor: 'rgba(0, 196, 140, 0.3)'
                },
                'intent': {
                    background: 'rgba(0, 180, 216, 0.1)',
                    color: '#00B4D8',
                    borderColor: 'rgba(0, 180, 216, 0.3)'
                },
                'none': {
                    background: 'rgba(156, 163, 175, 0.1)',
                    color: '#6B7280',
                    borderColor: 'rgba(156, 163, 175, 0.3)'
                }
            };
            return styles[matchType] || styles['none'];
        },

        // ========================================
        // Query Testing
        // ========================================
        async testQuery() {
            if (!this.queryForm.text.trim()) {
                this.showNotification('Please enter a question', 'error');
                return;
            }

            try {
                this.loading = true;
                this.queryResult = null;

                const endpoint = this.queryForm.method === 'hybrid'
                    ? '/retrieval/best_answer'
                    : `/retrieval/search_${this.queryForm.method}`;

                const response = await axios.post(
                    `${this.config.retrievalUrl}${endpoint}`,
                    {
                        query: this.queryForm.text,
                        language: this.queryForm.language,
                        top_k: 1
                    }
                );

                if (response.data) {
                    // Handle both single result and array results
                    const result = Array.isArray(response.data)
                        ? response.data[0]
                        : response.data;

                    if (result) {
                        this.queryResult = {
                            success: true,
                            data: result
                        };
                        this.showNotification('Match found!', 'success');
                    } else {
                        this.queryResult = {
                            success: false,
                            message: 'No matching FAQ found for your query.'
                        };
                        this.showNotification('No match found', 'warning');
                    }
                }
            } catch (error) {
                console.error('Query test failed:', error);
                this.queryResult = {
                    success: false,
                    message: error.response?.data?.detail || 'Query failed. Please check if services are running.'
                };
                this.showNotification('Query failed', 'error');
            } finally {
                this.loading = false;
            }
        },

        // ========================================
        // ASR Testing
        // ========================================
        handleAudioFile(event) {
            const file = event.target.files[0];
            if (file) {
                this.asrForm.audioFile = file;
                this.asrResult = null;
                this.queryResult = null;
            }
        },

        async testASR() {
            if (!this.asrForm.audioFile) {
                this.showNotification('Please select an audio file', 'error');
                return;
            }

            try {
                this.loading = true;
                this.asrResult = null;

                // Step 1: Transcribe audio
                const formData = new FormData();
                formData.append('file', this.asrForm.audioFile);
                formData.append('language', this.asrForm.language);

                console.log('Sending audio file:', this.asrForm.audioFile.name,
                           'Size:', this.asrForm.audioFile.size, 'bytes',
                           'Type:', this.asrForm.audioFile.type);

                const asrResponse = await axios.post(
                    `${this.config.asrUrl}/asr/transcribe`,
                    formData
                    // Let axios automatically set Content-Type with boundary
                );

                this.asrResult = asrResponse.data;
                this.showNotification('Audio transcribed successfully', 'success');

                // Step 2: Automatically search with transcribed text
                if (this.asrResult.text) {
                    this.queryForm.text = this.asrResult.text;
                    this.queryForm.language = this.asrResult.language;
                    await this.testQuery();
                }
            } catch (error) {
                console.error('ASR test failed:', error);
                this.showNotification(
                    error.response?.data?.detail || 'ASR transcription failed',
                    'error'
                );
            } finally {
                this.loading = false;
            }
        },

        // ========================================
        // Recording
        // ========================================
        async startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

                this.recording.mediaRecorder = new MediaRecorder(stream);
                this.recording.chunks = [];
                this.recording.duration = 0;

                this.recording.mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        this.recording.chunks.push(event.data);
                    }
                };

                this.recording.mediaRecorder.onstop = async () => {
                    // Check if we have recorded data
                    if (this.recording.chunks.length === 0) {
                        this.showNotification('No audio data recorded. Please try again.', 'error');
                        stream.getTracks().forEach(track => track.stop());
                        return;
                    }

                    const audioBlob = new Blob(this.recording.chunks, { type: 'audio/webm' });

                    // Validate blob size
                    if (audioBlob.size === 0) {
                        this.showNotification('Recording is empty. Please try again.', 'error');
                        stream.getTracks().forEach(track => track.stop());
                        return;
                    }

                    const audioFile = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });

                    // Set the recorded file as the audio file
                    this.asrForm.audioFile = audioFile;

                    // Stop all tracks
                    stream.getTracks().forEach(track => track.stop());

                    // Clear timer
                    if (this.recording.timer) {
                        clearInterval(this.recording.timer);
                        this.recording.timer = null;
                    }

                    this.showNotification(`Recording saved (${(audioBlob.size / 1024).toFixed(1)} KB). Transcribing...`, 'success');

                    // Automatically transcribe and search
                    await this.testASR();
                };

                // Start recording with timeslice to ensure data is captured
                this.recording.mediaRecorder.start(1000); // Capture data every 1 second
                this.recording.isRecording = true;

                // Start timer
                this.recording.timer = setInterval(() => {
                    this.recording.duration++;
                }, 1000);

                this.showNotification('Recording started', 'info');
            } catch (error) {
                console.error('Error accessing microphone:', error);
                this.showNotification(
                    'Error accessing microphone: ' + error.message +
                    '. Make sure you are using HTTPS or localhost.',
                    'error'
                );
            }
        },

        stopRecording() {
            if (this.recording.mediaRecorder && this.recording.isRecording) {
                this.recording.mediaRecorder.stop();
                this.recording.isRecording = false;
            }
        },

        // ========================================
        // Utilities
        // ========================================
        truncate(text, length) {
            if (text.length <= length) return text;
            return text.substring(0, length) + '...';
        },

        showNotification(message, type = 'info') {
            this.notification = {
                show: true,
                message,
                type
            };

            setTimeout(() => {
                this.notification.show = false;
            }, 3000);
        }
    },

    mounted() {
        this.init();

        // Refresh service status every 30 seconds
        setInterval(() => {
            this.checkServices();
        }, 30000);
    }
}).mount('#app');
