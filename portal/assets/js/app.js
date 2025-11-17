// SpeakSense Admin Portal - Vue.js Application

const { createApp } = Vue;

createApp({
    data() {
        return {
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
            asrResult: null
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
        }
    },

    methods: {
        // ========================================
        // Initialization
        // ========================================
        async init() {
            await this.checkServices();
            await this.refreshStats();
            await this.loadFAQs();
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
            this.faqForm = {
                question: '',
                answer: '',
                alternative_questions: [],
                language: 'auto',
                category: 'general'
            };
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
                formData.append('audio', this.asrForm.audioFile);
                formData.append('language', this.asrForm.language);

                const asrResponse = await axios.post(
                    `${this.config.asrUrl}/asr/transcribe`,
                    formData,
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    }
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
