public class InteractionSummaryService {
    
    public class InteractionSummaryException extends Exception {}
    
    @AuraEnabled(cacheable=false)
    public static String summarizeInteractions(Id accountId) {
        try {
            // Get interactions for the account
            List<Interaction__c> interactions = getInteractionsForAccount(accountId);
            
            if (interactions.isEmpty()) {
                throw new InteractionSummaryException('No interactions found for this account');
            }
            
            // Call AI service
            String summary = callAISummaryService(accountId, interactions);
            
            return summary;
            
        } catch (Exception e) {
            throw new AuraHandledException('Error generating summary: ' + e.getMessage());
        }
    }
    
    private static List<Interaction__c> getInteractionsForAccount(Id accountId) {
        return [
            SELECT Id, Account__c, Subject__c, Description__c, Interaction_Type__c, 
                   CreatedDate, CreatedBy.Name, Status__c, Priority__c
            FROM Interaction__c 
            WHERE Account__c = :accountId 
            ORDER BY CreatedDate DESC
            LIMIT 100
        ];
    }
    
    private static String callAISummaryService(Id accountId, List<Interaction__c> interactions) {
        try {
            // Prepare request payload
            Map<String, Object> requestBody = new Map<String, Object>();
            requestBody.put('account_id', accountId);
            
            List<Map<String, Object>> interactionList = new List<Map<String, Object>>();
            for (Interaction__c interaction : interactions) {
                Map<String, Object> interactionMap = new Map<String, Object>();
                interactionMap.put('id', interaction.Id);
                interactionMap.put('account_id', interaction.Account__c);
                interactionMap.put('subject', interaction.Subject__c);
                interactionMap.put('description', interaction.Description__c);
                interactionMap.put('interaction_type', interaction.Interaction_Type__c);
                interactionMap.put('created_date', interaction.CreatedDate.formatGMT('yyyy-MM-dd\'T\'HH:mm:ss\'Z\''));
                interactionMap.put('created_by', interaction.CreatedBy.Name);
                interactionMap.put('status', interaction.Status__c);
                interactionMap.put('priority', interaction.Priority__c);
                
                interactionList.add(interactionMap);
            }
            
            requestBody.put('interactions', interactionList);
            
            // Make HTTP callout
            Http http = new Http();
            HttpRequest request = new HttpRequest();
            request.setEndpoint('callout:AI_Summary_Service/summarize');
            request.setMethod('POST');
            request.setHeader('Content-Type', 'application/json');
            request.setBody(JSON.serialize(requestBody));
            request.setTimeout(60000); // 60 seconds timeout
            
            HttpResponse response = http.send(request);
            
            if (response.getStatusCode() == 200) {
                return response.getBody();
            } else {
                throw new InteractionSummaryException('AI service returned error: ' + response.getStatusCode() + ' - ' + response.getBody());
            }
            
        } catch (Exception e) {
            throw new InteractionSummaryException('Error calling AI service: ' + e.getMessage());
        }
    }
    
    // Test method with sample data
    @AuraEnabled(cacheable=false)
    public static String testSummarize() {
        try {
            Http http = new Http();
            HttpRequest request = new HttpRequest();
            request.setEndpoint('callout:AI_Summary_Service/test-summarize');
            request.setMethod('GET');
            request.setHeader('Content-Type', 'application/json');
            request.setTimeout(60000);
            
            HttpResponse response = http.send(request);
            
            if (response.getStatusCode() == 200) {
                return response.getBody();
            } else {
                throw new InteractionSummaryException('Test service returned error: ' + response.getStatusCode());
            }
            
        } catch (Exception e) {
            throw new AuraHandledException('Error testing AI service: ' + e.getMessage());
        }
    }
}
