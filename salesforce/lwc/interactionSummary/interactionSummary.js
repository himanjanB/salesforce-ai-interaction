import { LightningElement, api, track, wire } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { getRecord } from 'lightning/uiRecordApi';
import summarizeInteractions from '@salesforce/apex/InteractionSummaryService.summarizeInteractions';
import testSummarize from '@salesforce/apex/InteractionSummaryService.testSummarize';

const ACCOUNT_FIELDS = ['Account.Name'];

export default class InteractionSummary extends LightningElement {
    @api recordId; // Account ID
    @track isModalOpen = false;
    @track isLoading = false;
    @track summaryData = null;
    @track error = null;
    
    @wire(getRecord, { recordId: '$recordId', fields: ACCOUNT_FIELDS })
    account;
    
    get accountName() {
        return this.account?.data?.fields?.Name?.value || 'Account';
    }
    
    get hasSummary() {
        return this.summaryData !== null;
    }
    
    get modalTitle() {
        return `AI Summary for ${this.accountName}`;
    }
    
    get sentimentClass() {
        if (!this.summaryData) return 'neutral';
        
        const score = this.summaryData.sentiment_score;
        if (score > 0.1) return 'positive';
        if (score < -0.1) return 'negative';
        return 'neutral';
    }
    
    get sentimentLabel() {
        if (!this.summaryData) return 'Neutral';
        
        const score = this.summaryData.sentiment_score;
        if (score > 0.1) return 'Positive';
        if (score < -0.1) return 'Negative';
        return 'Neutral';
    }
    
    get urgencyVariant() {
        if (!this.summaryData) return 'base';
        
        const level = this.summaryData.urgency_level;
        if (level === 'High') return 'error';
        if (level === 'Medium') return 'warning';
        return 'success';
    }
    
    handleSummarize() {
        this.isModalOpen = true;
        this.isLoading = true;
        this.error = null;
        this.summaryData = null;
        
        // Call Apex method to get summary
        summarizeInteractions({ accountId: this.recordId })
            .then(result => {
                try {
                    const response = JSON.parse(result);
                    if (response.success) {
                        this.summaryData = response.summary;
                    } else {
                        this.error = response.error_message || 'Failed to generate summary';
                    }
                } catch (e) {
                    this.error = 'Error parsing summary response';
                }
            })
            .catch(error => {
                this.error = error.body?.message || 'Error generating summary';
                console.error('Error:', error);
            })
            .finally(() => {
                this.isLoading = false;
            });
    }
    
    handleTestSummarize() {
        this.isModalOpen = true;
        this.isLoading = true;
        this.error = null;
        this.summaryData = null;
        
        // Call test method
        testSummarize()
            .then(result => {
                try {
                    const response = JSON.parse(result);
                    if (response.success) {
                        this.summaryData = response.summary;
                    } else {
                        this.error = response.error_message || 'Failed to generate test summary';
                    }
                } catch (e) {
                    this.error = 'Error parsing test summary response';
                }
            })
            .catch(error => {
                this.error = error.body?.message || 'Error generating test summary';
                console.error('Error:', error);
            })
            .finally(() => {
                this.isLoading = false;
            });
    }
    
    handleCloseModal() {
        this.isModalOpen = false;
        this.summaryData = null;
        this.error = null;
    }
    
    showToast(title, message, variant) {
        const evt = new ShowToastEvent({
            title: title,
            message: message,
            variant: variant
        });
        this.dispatchEvent(evt);
    }
}
