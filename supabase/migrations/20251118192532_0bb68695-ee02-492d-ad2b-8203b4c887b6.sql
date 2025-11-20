-- Create user profiles table
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT,
  full_name TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON public.profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

-- Create enum for document types
CREATE TYPE public.document_type AS ENUM ('word', 'powerpoint');

-- Create enum for project status
CREATE TYPE public.project_status AS ENUM ('draft', 'generating', 'completed');

-- Create projects table
CREATE TABLE public.projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  document_type public.document_type NOT NULL,
  topic TEXT NOT NULL,
  status public.project_status DEFAULT 'draft',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

-- Projects policies
CREATE POLICY "Users can view own projects"
  ON public.projects FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own projects"
  ON public.projects FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own projects"
  ON public.projects FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own projects"
  ON public.projects FOR DELETE
  USING (auth.uid() = user_id);

-- Create sections table (for document sections or slides)
CREATE TABLE public.sections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  content TEXT,
  order_index INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.sections ENABLE ROW LEVEL SECURITY;

-- Sections policies
CREATE POLICY "Users can view sections of own projects"
  ON public.sections FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.projects
      WHERE projects.id = sections.project_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert sections to own projects"
  ON public.sections FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.projects
      WHERE projects.id = sections.project_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update sections of own projects"
  ON public.sections FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.projects
      WHERE projects.id = sections.project_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete sections of own projects"
  ON public.sections FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.projects
      WHERE projects.id = sections.project_id
      AND projects.user_id = auth.uid()
    )
  );

-- Create refinements table (history of AI edits)
CREATE TABLE public.refinements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  section_id UUID NOT NULL REFERENCES public.sections(id) ON DELETE CASCADE,
  prompt TEXT NOT NULL,
  result TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.refinements ENABLE ROW LEVEL SECURITY;

-- Refinements policies
CREATE POLICY "Users can view refinements of own sections"
  ON public.refinements FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.sections
      INNER JOIN public.projects ON sections.project_id = projects.id
      WHERE sections.id = refinements.section_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert refinements to own sections"
  ON public.refinements FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.sections
      INNER JOIN public.projects ON sections.project_id = projects.id
      WHERE sections.id = refinements.section_id
      AND projects.user_id = auth.uid()
    )
  );

-- Create feedback table (likes/dislikes and comments)
CREATE TABLE public.feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  section_id UUID NOT NULL REFERENCES public.sections(id) ON DELETE CASCADE,
  is_liked BOOLEAN,
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;

-- Feedback policies
CREATE POLICY "Users can view feedback on own sections"
  ON public.feedback FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.sections
      INNER JOIN public.projects ON sections.project_id = projects.id
      WHERE sections.id = feedback.section_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert feedback on own sections"
  ON public.feedback FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.sections
      INNER JOIN public.projects ON sections.project_id = projects.id
      WHERE sections.id = feedback.section_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update feedback on own sections"
  ON public.feedback FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.sections
      INNER JOIN public.projects ON sections.project_id = projects.id
      WHERE sections.id = feedback.section_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete feedback on own sections"
  ON public.feedback FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.sections
      INNER JOIN public.projects ON sections.project_id = projects.id
      WHERE sections.id = feedback.section_id
      AND projects.user_id = auth.uid()
    )
  );

-- Create function to handle new user signups
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    NEW.raw_user_meta_data->>'full_name'
  );
  RETURN NEW;
END;
$$;

-- Create trigger for new user signups
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

-- Create triggers for updated_at
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_projects_updated_at
  BEFORE UPDATE ON public.projects
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_sections_updated_at
  BEFORE UPDATE ON public.sections
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_feedback_updated_at
  BEFORE UPDATE ON public.feedback
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();