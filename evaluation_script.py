import json
import csv
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy import stats

def generate_mock_data(n_pairs=50):
    """
    Generates 50 mock resume-job pairs simulating unstructured data.
    """
    domains = ["Backend Engineering", "Frontend Development", "Data Science", "Machine Learning", "DevOps"]
    skills_pool = ["Python", "React", "Node.js", "Docker", "AWS", "SQL", "MongoDB", "Kubernetes", "FastAPI", "TypeScript"]
    
    pairs = []
    for _ in range(n_pairs):
        domain = random.choice(domains)
        job_skills = random.sample(skills_pool, k=random.randint(3, 7))
        resume_skills = random.sample(skills_pool, k=random.randint(3, 7))
        
        job_desc = f"Looking for a {domain} professional. Requirements include {' '.join(job_skills)}. Must build robust systems."
        resume_desc = f"Experienced in {domain}. Specialized in {' '.join(resume_skills)}. Built sophisticated applications."
        
        # Simulating parsed alignment properties
        title_alignment = 1.0 if domain in resume_desc else 0.5
        recency_score = random.uniform(0.7, 1.0)
        
        pairs.append({
            "job_desc": job_desc,
            "resume_desc": resume_desc,
            "job_skills": set(job_skills),
            "resume_skills": set(resume_skills),
            "title_alignment": title_alignment,
            "recency_score": recency_score
        })
    return pairs

def compute_cosine_tfidf(doc1, doc2):
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform([doc1, doc2])
        return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except ValueError:
        return 0.0

def evaluate_pairs(pairs):
    results = []
    
    for idx, p in enumerate(pairs):
        # 1. Base Metric: Semantic TF-IDF Cosine Similarity
        cosine_sim = compute_cosine_tfidf(p["job_desc"], p["resume_desc"])
        
        # 2. Strict Skill Overlap
        overlap_count = len(p["job_skills"].intersection(p["resume_skills"]))
        skill_overlap_score = overlap_count / len(p["job_skills"]) if p["job_skills"] else 0.0
        
        # 3. Coverage
        coverage_score = skill_overlap_score * 0.9 # Minor coverage modifier
        
        # --- THE BASELINE MODEL (TF-IDF keyword-only) ---
        baseline_score = cosine_sim
        
        # --- THE GOLD STANDARD COMPOSITE (6-Signal System) ---
        # 40% TF-IDF, 25% Overlap, 15% Title Focus, 10% Coverage, 5% Alignment Penalty, 5% Recency
        composite_score = (
            (cosine_sim * 0.40) +
            (skill_overlap_score * 0.25) +
            (p["title_alignment"] * 0.15) +
            (coverage_score * 0.10) +
            (p["title_alignment"] * 0.05) + # representing alignment penalty inversion
            (p["recency_score"] * 0.05)
        )
        
        # --- TASK 2: PER-SIGNAL ABLATION SCORES (Removing specific signals) ---
        ablation_no_similarity = composite_score - (cosine_sim * 0.40)
        ablation_no_overlap = composite_score - (skill_overlap_score * 0.25)
        ablation_no_title = composite_score - (p["title_alignment"] * 0.15)
        
        # --- TASK 5: PAIRED DIFFERENCE (Composite vs Baseline) ---
        paired_diff = composite_score - baseline_score
        
        results.append({
            "pair_id": idx + 1,
            "baseline_tfidf": round(baseline_score, 4),
            "gold_composite": round(composite_score, 4),
            "paired_difference": round(paired_diff, 4),
            "ablation_no_sim": round(ablation_no_similarity, 4),
            "ablation_no_skills": round(ablation_no_overlap, 4),
            "ablation_no_title": round(ablation_no_title, 4)
        })
        
    return results

def main():
    print("Generating 50 Resume-Job Pairs...")
    pairs = generate_mock_data(50)
    
    print("Evaluating models and computing ablation studies...")
    evaluated_data = evaluate_pairs(pairs)
    
    # Statistical T-Test Feed (Task 5)
    baselines = [d["baseline_tfidf"] for d in evaluated_data]
    composites = [d["gold_composite"] for d in evaluated_data]
    
    # Paired Student's T-Test
    t_stat, p_value = stats.ttest_rel(composites, baselines)
    
    print(f"\n--- Statistical Evaluation Results (Task 5) ---")
    print(f"Paired T-Test Statistic: {t_stat:.4f}")
    print(f"P-Value: {p_value:.6e}")
    print(f"Significance: {'Statistically Significant' if p_value < 0.05 else 'Not Significant'} at alpha=0.05")
    
    # Saving to structured files for research reporting
    csv_file = "evaluation_metrics_tasks_2_5.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=evaluated_data[0].keys())
        writer.writeheader()
        writer.writerows(evaluated_data)
        
    print(f"\nMetrics successfully exported to {csv_file}")
    
if __name__ == "__main__":
    main()
