import axios from 'axios';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const lmsApi = axios.create({ baseURL: API });

lmsApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('ncct_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export type MyCourse = {
  course_id: number;
  course_code: string;
  title: string;
  programme_id: number;
  total_lessons: number;
  completed_lessons: number;
  progress_percent: number;
};

export type Lesson = {
  id: number;
  module_id: number;
  lesson_number: number;
  title: string;
  content_type: string;
  content_url?: string;
  duration_minutes: number;
  is_mandatory: boolean;
  status: string;
  assessment_id?: number;
  assessment_title?: string;
  assessment_question_count: number;
  assessment_pass_mark?: number;
};

export type CourseModule = {
  id: number;
  course_id: number;
  module_number: number;
  title: string;
  learning_objectives?: string;
  duration_minutes: number;
  lessons: Lesson[];
};

export type CourseDetail = {
  id: number;
  programme_id: number;
  course_code: string;
  title: string;
  description?: string;
  category: string;
  delivery_mode: string;
  duration_hours: number;
  level: string;
  status: string;
  modules: CourseModule[];
  total_lessons: number;
  completed_lessons: number;
  progress_percent: number;
};

export type LessonProgress = {
  id: number;
  trainee_id: number;
  lesson_id: number;
  status: string;
  started_at?: string;
  completed_at?: string;
  last_accessed_at?: string;
};

export type AssessmentOption = {
  id: number;
  option_number: number;
  option_text: string;
};

export type AssessmentQuestion = {
  id: number;
  question_number: number;
  question_text: string;
  marks: number;
  options: AssessmentOption[];
};

export type Assessment = {
  id: number;
  lesson_id: number;
  title: string;
  instructions?: string;
  pass_mark: number;
  max_attempts: number;
  status: string;
  question_count: number;
  max_score: number;
  questions: AssessmentQuestion[];
};

export type AssessmentAttempt = {
  id: number;
  assessment_id: number;
  trainee_id: number;
  attempt_number: number;
  score: number;
  max_score: number;
  percentage: number;
  result: string;
  submitted_at: string;
};

export async function getMyCourses() {
  return (await lmsApi.get<MyCourse[]>('/lms/my-courses')).data;
}

export async function getCourse(courseId: number) {
  return (await lmsApi.get<CourseDetail>(`/lms/courses/${courseId}`)).data;
}

export async function getCourseProgress(courseId: number) {
  return (await lmsApi.get<LessonProgress[]>(`/lms/courses/${courseId}/progress`)).data;
}

export async function startLesson(lessonId: number) {
  return (await lmsApi.post<LessonProgress>(`/lms/lessons/${lessonId}/start`)).data;
}

export async function completeLesson(lessonId: number) {
  return (await lmsApi.post<LessonProgress>(`/lms/lessons/${lessonId}/complete`)).data;
}

export async function getLessonAssessment(lessonId: number) {
  return (await lmsApi.get<Assessment>(`/lms/lessons/${lessonId}/assessment`)).data;
}

export async function submitAssessment(assessmentId: number, answers: { question_id: number; selected_option_id?: number }[]) {
  return (await lmsApi.post<AssessmentAttempt>(`/lms/assessments/${assessmentId}/submit`, { answers })).data;
}

export async function getLatestAssessmentResult(assessmentId: number) {
  return (await lmsApi.get<AssessmentAttempt>(`/lms/assessments/${assessmentId}/result`)).data;
}
