import pandas as pd
import numpy as np
import re
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Any
import logging

# Try to import tldextract, fall back to manual domain parsing if not available
try:
    import tldextract
    TLDEXTRACT_AVAILABLE = True
except ImportError:
    TLDEXTRACT_AVAILABLE = False
    print("Warning: tldextract not available. Using fallback domain parsing.")

try:
    import validators
    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False
    print("Warning: validators not available. Using basic URL validation.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class URLFeatureExtractor:
    """
    Extract comprehensive features from URLs for phishing detection
    """
    
    def __init__(self):
        # Common phishing keywords
        self.phishing_keywords = [
            'login', 'signin', 'account', 'update', 'secure', 'banking', 'paypal',
            'amazon', 'microsoft', 'google', 'apple', 'verify', 'suspended',
            'limited', 'confirm', 'security', 'alert', 'notification'
        ]
        
        # Suspicious TLD patterns
        self.suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.pw', '.click', '.download']
        
        # Common legitimate domains for reference
        self.legitimate_domains = [
            'google.com', 'facebook.com', 'amazon.com', 'microsoft.com', 
            'apple.com', 'twitter.com', 'linkedin.com', 'github.com'
        ]

    def extract_basic_features(self, url: str) -> Dict[str, Any]:
        """Extract basic URL structure features"""
        features = {}
        
        try:
            # Basic length features
            features['url_length'] = len(url)
            features['domain_length'] = len(self._extract_domain(url))
            
            # Parse URL components
            parsed = urlparse(url)
            features['has_https'] = 1 if parsed.scheme == 'https' else 0
            features['has_www'] = 1 if parsed.netloc.startswith('www.') else 0
            
            # Path analysis
            features['path_length'] = len(parsed.path)
            features['num_path_segments'] = len([x for x in parsed.path.split('/') if x])
            
            # Query parameters
            features['has_query'] = 1 if parsed.query else 0
            features['query_length'] = len(parsed.query)
            features['num_query_params'] = len(parse_qs(parsed.query))
            
            # Fragment
            features['has_fragment'] = 1 if parsed.fragment else 0
            features['fragment_length'] = len(parsed.fragment)
            
        except Exception as e:
            logger.warning(f"Error extracting basic features for {url}: {e}")
            # Set default values
            features.update({
                'url_length': 0, 'domain_length': 0, 'has_https': 0,
                'has_www': 0, 'path_length': 0, 'num_path_segments': 0,
                'has_query': 0, 'query_length': 0, 'num_query_params': 0,
                'has_fragment': 0, 'fragment_length': 0
            })
        
        return features

    def extract_domain_features(self, url: str) -> Dict[str, Any]:
        """Extract domain-specific features"""
        features = {}
        
        try:
            if TLDEXTRACT_AVAILABLE:
                extracted = tldextract.extract(url)
                domain = extracted.domain
                subdomain = extracted.subdomain
                suffix = extracted.suffix
                fqdn = extracted.fqdn
            else:
                # Fallback manual parsing
                parsed = urlparse(url)
                netloc = parsed.netloc.lower()
                parts = netloc.split('.')
                
                if len(parts) >= 2:
                    suffix = parts[-1]
                    domain = parts[-2]
                    subdomain = '.'.join(parts[:-2]) if len(parts) > 2 else ''
                    fqdn = netloc
                else:
                    suffix = ''
                    domain = netloc
                    subdomain = ''
                    fqdn = netloc
            
            # Domain analysis
            features['num_subdomains'] = len(subdomain.split('.')) if subdomain else 0
            features['subdomain_length'] = len(subdomain)
            features['domain_has_numbers'] = 1 if re.search(r'\d', domain) else 0
            features['domain_has_hyphens'] = 1 if '-' in domain else 0
            
            # TLD analysis
            features['suspicious_tld'] = 1 if f'.{suffix}' in self.suspicious_tlds else 0
            features['tld_length'] = len(suffix)
            
            # IP address check
            features['is_ip_address'] = 1 if self._is_ip_address(fqdn) else 0
            
            # Domain reputation (basic check)
            full_domain = f"{domain}.{suffix}" if suffix else domain
            features['is_known_legitimate'] = 1 if full_domain in self.legitimate_domains else 0
            
        except Exception as e:
            logger.warning(f"Error extracting domain features for {url}: {e}")
            features.update({
                'num_subdomains': 0, 'subdomain_length': 0, 'domain_has_numbers': 0,
                'domain_has_hyphens': 0, 'suspicious_tld': 0, 'tld_length': 0,
                'is_ip_address': 0, 'is_known_legitimate': 0
            })
        
        return features

    def extract_suspicious_patterns(self, url: str) -> Dict[str, Any]:
        """Extract features based on suspicious patterns"""
        features = {}
        
        url_lower = url.lower()
        
        # Character-based features
        features['num_dots'] = url.count('.')
        features['num_hyphens'] = url.count('-')
        features['num_underscores'] = url.count('_')
        features['num_slashes'] = url.count('/')
        features['num_question_marks'] = url.count('?')
        features['num_equal_signs'] = url.count('=')
        features['num_at_signs'] = url.count('@')
        features['num_ampersands'] = url.count('&')
        
        # Suspicious character patterns
        features['has_punycode'] = 1 if 'xn--' in url_lower else 0
        features['has_suspicious_chars'] = 1 if re.search(r'[<>"\{\}|\\^`\[\]]', url) else 0
        
        # URL shorteners (often used in phishing)
        shorteners = ['bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'short.link']
        features['is_shortened'] = 1 if any(shortener in url_lower for shortener in shorteners) else 0
        
        # Phishing keywords
        features['num_phishing_keywords'] = sum(1 for keyword in self.phishing_keywords if keyword in url_lower)
        features['has_phishing_keywords'] = 1 if features['num_phishing_keywords'] > 0 else 0
        
        # Homograph attacks (basic detection)
        features['has_homograph_chars'] = 1 if self._has_homograph_chars(url) else 0
        
        # Double redirects or suspicious redirections
        features['has_redirect_patterns'] = 1 if re.search(r'(redirect|redir|goto|url=http)', url_lower) else 0
        
        return features

    def extract_entropy_features(self, url: str) -> Dict[str, Any]:
        """Extract entropy-based features"""
        features = {}
        
        try:
            # Calculate entropy of different URL parts
            parsed = urlparse(url)
            
            features['url_entropy'] = self._calculate_entropy(url)
            features['domain_entropy'] = self._calculate_entropy(parsed.netloc)
            features['path_entropy'] = self._calculate_entropy(parsed.path) if parsed.path else 0
            
            # Character distribution
            features['vowel_ratio'] = self._calculate_vowel_ratio(url)
            features['digit_ratio'] = len(re.findall(r'\d', url)) / len(url) if url else 0
            features['special_char_ratio'] = len(re.findall(r'[^a-zA-Z0-9]', url)) / len(url) if url else 0
            
        except Exception as e:
            logger.warning(f"Error calculating entropy features for {url}: {e}")
            features.update({
                'url_entropy': 0, 'domain_entropy': 0, 'path_entropy': 0,
                'vowel_ratio': 0, 'digit_ratio': 0, 'special_char_ratio': 0
            })
        
        return features

    def extract_all_features(self, url: str) -> Dict[str, Any]:
        """Extract all features from a URL"""
        all_features = {}
        
        # Combine all feature extraction methods
        all_features.update(self.extract_basic_features(url))
        all_features.update(self.extract_domain_features(url))
        all_features.update(self.extract_suspicious_patterns(url))
        all_features.update(self.extract_entropy_features(url))
        
        return all_features

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc
        except:
            return ""

    def _is_ip_address(self, domain: str) -> bool:
        """Check if domain is an IP address"""
        ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return bool(re.match(ip_pattern, domain))

    def _has_homograph_chars(self, url: str) -> bool:
        """Basic detection of homograph characters"""
        # This is a simplified check - in practice, you'd want a more comprehensive list
        homograph_chars = ['а', 'е', 'о', 'р', 'у', 'х']  # Cyrillic chars that look like Latin
        return any(char in url for char in homograph_chars)

    def _calculate_entropy(self, string: str) -> float:
        """Calculate Shannon entropy of a string"""
        if not string:
            return 0
        
        # Calculate frequency of each character
        char_counts = {}
        for char in string:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Calculate entropy
        length = len(string)
        entropy = 0
        for count in char_counts.values():
            p = count / length
            if p > 0:
                entropy -= p * np.log2(p)
        
        return entropy

    def _calculate_vowel_ratio(self, string: str) -> float:
        """Calculate ratio of vowels in string"""
        if not string:
            return 0
        
        vowels = 'aeiouAEIOU'
        vowel_count = sum(1 for char in string if char in vowels)
        return vowel_count / len(string)


class DataPreprocessor:
    """
    Main class for preprocessing the phishing URL dataset
    """
    
    def __init__(self):
        self.feature_extractor = URLFeatureExtractor()
    
    def load_dataset(self, file_path: str, url_column: str = 'url', label_column: str = 'label') -> pd.DataFrame:
        """
        Load dataset from CSV file
        Expected format: URL, Label (where Label is 0 for legitimate, 1 for phishing)
        """
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded dataset with {len(df)} samples")
            
            # Validate required columns
            if url_column not in df.columns:
                raise ValueError(f"URL column '{url_column}' not found in dataset")
            if label_column not in df.columns:
                raise ValueError(f"Label column '{label_column}' not found in dataset")
            
            # Rename columns for consistency
            df = df.rename(columns={url_column: 'url', label_column: 'label'})
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            raise

    def preprocess_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the entire dataset by extracting features from URLs
        """
        logger.info("Starting feature extraction...")
        
        # Extract features for all URLs
        features_list = []
        for idx, row in df.iterrows():
            if idx % 1000 == 0:
                logger.info(f"Processed {idx}/{len(df)} URLs")
            
            url = row['url']
            features = self.feature_extractor.extract_all_features(url)
            features['label'] = row['label']
            features_list.append(features)
        
        # Convert to DataFrame
        processed_df = pd.DataFrame(features_list)
        logger.info(f"Feature extraction complete. Shape: {processed_df.shape}")
        
        return processed_df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the processed dataset
        """
        logger.info("Cleaning dataset...")
        
        # Remove rows with missing critical features
        initial_size = len(df)
        df = df.dropna()
        logger.info(f"Removed {initial_size - len(df)} rows with missing values")
        
        # Remove duplicate URLs if any
        df = df.drop_duplicates()
        logger.info(f"Final dataset size: {len(df)}")
        
        return df

    def save_processed_data(self, df: pd.DataFrame, output_path: str):
        """
        Save processed dataset to CSV
        """
        df.to_csv(output_path, index=False)
        logger.info(f"Saved processed dataset to {output_path}")


if __name__ == "__main__":
    # Example usage
    preprocessor = DataPreprocessor()
    
    # You would load your dataset here
    # df = preprocessor.load_dataset("path/to/your/phishing_urls.csv")
    # processed_df = preprocessor.preprocess_dataset(df)
    # cleaned_df = preprocessor.clean_data(processed_df)
    # preprocessor.save_processed_data(cleaned_df, "data/processed_features.csv")
    
    print("Data preprocessing module ready!")
