#!/usr/bin/env python3
"""
Advanced URL Analysis Tool - Comprehensive phishing detection with detailed reporting
"""

import sys
import os
import json
import csv
from pathlib import Path
from datetime import datetime
import time

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.preprocessing import URLFeatureExtractor
    from app.ml_model import PhishingDetectionModel
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

class AdvancedURLAnalyzer:
    """Advanced URL analysis with comprehensive reporting"""
    
    def __init__(self, model_path="models/phishing_detector.joblib"):
        self.feature_extractor = URLFeatureExtractor()
        self.model = PhishingDetectionModel()
        self.model_path = model_path
        self.model_loaded = False
        
        # Load model if available
        if Path(model_path).exists():
            try:
                self.model.load_model(model_path)
                self.model_loaded = True
                print(f"✓ Loaded model: {self.model.model_type}")
            except Exception as e:
                print(f"✗ Failed to load model: {e}")
        else:
            print(f"✗ Model not found: {model_path}")
    
    def analyze_url(self, url, detailed=True):
        """Comprehensive URL analysis"""
        analysis = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'analysis_time_ms': 0,
            'features': {},
            'prediction': {},
            'risk_assessment': {},
            'recommendations': []
        }
        
        start_time = time.time()
        
        try:
            # Extract features
            features = self.feature_extractor.extract_all_features(url)
            analysis['features'] = features
            
            if self.model_loaded:
                # Make prediction
                prediction = self.model.predict(features)
                analysis['prediction'] = prediction
                
                # Risk assessment
                analysis['risk_assessment'] = self._assess_risk(features, prediction)
                
                # Generate recommendations
                analysis['recommendations'] = self._generate_recommendations(features, prediction)
            
            analysis['analysis_time_ms'] = round((time.time() - start_time) * 1000, 2)
            analysis['success'] = True
            
        except Exception as e:
            analysis['error'] = str(e)
            analysis['success'] = False
        
        return analysis
    
    def _assess_risk(self, features, prediction):
        """Detailed risk assessment"""
        risk_factors = []
        
        # Check suspicious patterns
        if features.get('num_phishing_keywords', 0) > 0:
            risk_factors.append(f"Contains {features['num_phishing_keywords']} phishing keywords")
        
        if features.get('url_length', 0) > 100:
            risk_factors.append(f"Unusually long URL ({features['url_length']} characters)")
        
        if features.get('has_https', 1) == 0:
            risk_factors.append("No HTTPS encryption")
        
        if features.get('num_dots', 0) > 5:
            risk_factors.append(f"Many subdomains ({features['num_dots']} dots)")
        
        if features.get('is_shortened', 0) == 1:
            risk_factors.append("URL shortener detected")
        
        if features.get('suspicious_tld', 0) == 1:
            risk_factors.append("Suspicious top-level domain")
        
        if features.get('is_ip_address', 0) == 1:
            risk_factors.append("Uses IP address instead of domain")
        
        # Risk level
        prob = prediction.get('phishing_probability', 0)
        if prob >= 0.8:
            risk_level = "CRITICAL"
            color = "🔴"
        elif prob >= 0.6:
            risk_level = "HIGH"
            color = "🟠"
        elif prob >= 0.4:
            risk_level = "MEDIUM"
            color = "🟡"
        elif prob >= 0.2:
            risk_level = "LOW"
            color = "🟢"
        else:
            risk_level = "MINIMAL"
            color = "🟢"
        
        return {
            'risk_level': risk_level,
            'risk_color': color,
            'probability': prob,
            'confidence': prediction.get('confidence', 0),
            'risk_factors': risk_factors,
            'factor_count': len(risk_factors)
        }
    
    def _generate_recommendations(self, features, prediction):
        """Generate security recommendations"""
        recommendations = []
        
        if prediction.get('is_phishing', False):
            recommendations.extend([
                "🚨 DO NOT enter personal information on this site",
                "🚨 DO NOT download files from this URL", 
                "🚨 Close this page immediately",
                "📞 Report this URL to security authorities"
            ])
        
        if features.get('has_https', 1) == 0:
            recommendations.append("⚠️ Avoid entering sensitive data on non-HTTPS sites")
        
        if features.get('num_phishing_keywords', 0) > 2:
            recommendations.append("⚠️ Be suspicious of urgent security/account messages")
        
        if features.get('is_shortened', 0) == 1:
            recommendations.append("⚠️ Verify destination of shortened URLs before clicking")
        
        if prediction.get('phishing_probability', 0) < 0.3:
            recommendations.extend([
                "✅ URL appears legitimate, but remain vigilant",
                "🔍 Verify domain spelling and SSL certificate",
                "🛡️ Keep antivirus software updated"
            ])
        
        return recommendations
    
    def batch_analyze(self, urls, output_file=None, detailed=True):
        """Analyze multiple URLs"""
        print(f"🔍 Analyzing {len(urls)} URLs...")
        
        results = []
        high_risk_count = 0
        
        for i, url in enumerate(urls, 1):
            print(f"Processing {i}/{len(urls)}: {url[:50]}...")
            
            analysis = self.analyze_url(url, detailed)
            results.append(analysis)
            
            # Count high-risk URLs
            if analysis.get('risk_assessment', {}).get('risk_level') in ['CRITICAL', 'HIGH']:
                high_risk_count += 1
        
        # Summary
        summary = {
            'total_analyzed': len(urls),
            'high_risk_count': high_risk_count,
            'analysis_timestamp': datetime.now().isoformat(),
            'model_type': self.model.model_type if self.model_loaded else 'None'
        }
        
        batch_results = {
            'summary': summary,
            'results': results
        }
        
        # Save to file if specified
        if output_file:
            self.save_results(batch_results, output_file)
        
        return batch_results
    
    def save_results(self, results, filename):
        """Save analysis results to file"""
        file_path = Path(filename)
        
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        elif file_path.suffix.lower() == '.csv':
            self._save_to_csv(results, file_path)
        else:
            # Default to JSON
            with open(file_path.with_suffix('.json'), 'w') as f:
                json.dump(results, f, indent=2, default=str)
        
        print(f"✓ Results saved to {file_path}")
    
    def _save_to_csv(self, results, file_path):
        """Save results to CSV format"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'URL', 'Is_Phishing', 'Phishing_Probability', 'Risk_Level',
                'Confidence', 'URL_Length', 'Has_HTTPS', 'Phishing_Keywords',
                'Num_Dots', 'Risk_Factors', 'Analysis_Time_MS'
            ])
            
            # Data
            for result in results.get('results', []):
                if result.get('success', False):
                    features = result.get('features', {})
                    prediction = result.get('prediction', {})
                    risk = result.get('risk_assessment', {})
                    
                    writer.writerow([
                        result['url'],
                        prediction.get('is_phishing', False),
                        round(prediction.get('phishing_probability', 0), 4),
                        risk.get('risk_level', 'Unknown'),
                        round(prediction.get('confidence', 0), 4),
                        features.get('url_length', 0),
                        features.get('has_https', 0),
                        features.get('num_phishing_keywords', 0),
                        features.get('num_dots', 0),
                        '; '.join(risk.get('risk_factors', [])),
                        result.get('analysis_time_ms', 0)
                    ])
    
    def generate_report(self, analysis_results, output_file="security_report.html"):
        """Generate HTML security report"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Phishing Detection Security Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }
        .summary { background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 8px; }
        .url-analysis { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 8px; }
        .high-risk { border-left: 5px solid #e74c3c; background: #fdf2f2; }
        .medium-risk { border-left: 5px solid #f39c12; background: #fef9e7; }
        .low-risk { border-left: 5px solid #27ae60; background: #eafaf1; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 10px 0; }
        .feature { background: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 0.9em; }
        .recommendations { background: #e8f4fd; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Phishing Detection Security Report</h1>
        <p>Generated on {timestamp}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Summary</h2>
        <p><strong>Total URLs Analyzed:</strong> {total_analyzed}</p>
        <p><strong>High Risk URLs:</strong> {high_risk_count}</p>
        <p><strong>Model Used:</strong> {model_type}</p>
    </div>
    
    {url_analyses}
</body>
</html>
        """
        
        url_analyses = ""
        for result in analysis_results.get('results', []):
            if result.get('success', False):
                risk = result.get('risk_assessment', {})
                risk_class = risk.get('risk_level', 'LOW').lower() + '-risk'
                
                url_analyses += f"""
                <div class="url-analysis {risk_class}">
                    <h3>{risk.get('risk_color', '🔍')} {result['url']}</h3>
                    <p><strong>Risk Level:</strong> {risk.get('risk_level', 'Unknown')} 
                       ({risk.get('probability', 0):.1%} phishing probability)</p>
                    
                    <div class="features">
                        <div class="feature">Length: {result['features'].get('url_length', 0)} chars</div>
                        <div class="feature">HTTPS: {'Yes' if result['features'].get('has_https') else 'No'}</div>
                        <div class="feature">Keywords: {result['features'].get('num_phishing_keywords', 0)}</div>
                        <div class="feature">Subdomains: {result['features'].get('num_dots', 0)}</div>
                    </div>
                    
                    {f"<div class='recommendations'><strong>⚠️ Risk Factors:</strong><br>{'<br>'.join(risk.get('risk_factors', []))}</div>" if risk.get('risk_factors') else ""}
                    
                    {f"<div class='recommendations'><strong>🛡️ Recommendations:</strong><br>{'<br>'.join(result.get('recommendations', []))}</div>" if result.get('recommendations') else ""}
                </div>
                """
        
        html_content = html_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_analyzed=analysis_results.get('summary', {}).get('total_analyzed', 0),
            high_risk_count=analysis_results.get('summary', {}).get('high_risk_count', 0),
            model_type=analysis_results.get('summary', {}).get('model_type', 'Unknown'),
            url_analyses=url_analyses
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ HTML report generated: {output_file}")

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced URL Phishing Analysis Tool')
    parser.add_argument('--url', help='Single URL to analyze')
    parser.add_argument('--file', help='File containing URLs (one per line)')
    parser.add_argument('--output', help='Output file for results')
    parser.add_argument('--format', choices=['json', 'csv', 'html'], default='json', 
                       help='Output format')
    parser.add_argument('--detailed', action='store_true', help='Include detailed analysis')
    
    args = parser.parse_args()
    
    analyzer = AdvancedURLAnalyzer()
    
    if not analyzer.model_loaded:
        print("⚠️ Warning: No model loaded. Only feature extraction will be performed.")
    
    if args.url:
        # Single URL analysis
        print(f"🔍 Analyzing URL: {args.url}")
        result = analyzer.analyze_url(args.url, args.detailed)
        
        if args.output:
            analyzer.save_results({'results': [result]}, args.output)
        else:
            print(json.dumps(result, indent=2, default=str))
    
    elif args.file:
        # Batch analysis
        if not Path(args.file).exists():
            print(f"❌ File not found: {args.file}")
            return
        
        with open(args.file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        results = analyzer.batch_analyze(urls, args.output, args.detailed)
        
        if args.format == 'html':
            html_file = args.output or "analysis_report.html"
            analyzer.generate_report(results, html_file)
        
        # Print summary
        summary = results.get('summary', {})
        print(f"\n📊 ANALYSIS COMPLETE:")
        print(f"   Total URLs: {summary.get('total_analyzed', 0)}")
        print(f"   High Risk: {summary.get('high_risk_count', 0)}")
    
    else:
        # Interactive mode
        print("🔍 Advanced URL Analyzer - Interactive Mode")
        print("Enter URLs to analyze (or 'quit' to exit):")
        
        while True:
            url = input("\nURL> ").strip()
            if url.lower() in ['quit', 'exit', 'q']:
                break
            if url:
                result = analyzer.analyze_url(url, True)
                
                if result.get('success'):
                    risk = result.get('risk_assessment', {})
                    print(f"\n{risk.get('risk_color', '🔍')} Risk Level: {risk.get('risk_level', 'Unknown')}")
                    print(f"📊 Phishing Probability: {risk.get('probability', 0):.1%}")
                    print(f"⏱️ Analysis Time: {result.get('analysis_time_ms', 0)}ms")
                    
                    if risk.get('risk_factors'):
                        print(f"⚠️ Risk Factors:")
                        for factor in risk['risk_factors']:
                            print(f"   • {factor}")
                    
                    if result.get('recommendations'):
                        print(f"🛡️ Recommendations:")
                        for rec in result['recommendations']:
                            print(f"   • {rec}")
                else:
                    print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
