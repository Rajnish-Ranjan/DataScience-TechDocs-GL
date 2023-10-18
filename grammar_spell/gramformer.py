# https://github.com/PrithivirajDamodaran/Gramformer.git

class Gramformer:

  def __init__(self, use_gpu=False):
    import torch

    def set_seed(seed):
       torch.manual_seed(seed)
       if torch.cuda.is_available():
          torch.cuda.manual_seed_all(seed)

    set_seed(1212)

    import errant
    self.annotator = errant.load('en')
    
    if use_gpu:
        device= "cuda:0"
    else:
        device = "cpu"
    batch_size = 1
    self.device    = device
    correction_model_tag = "prithivida/grammar_error_correcter_v1"
    self.model_loaded = False

    self.correction_tokenizer = torch.load("./corr_token")
    self.correction_model = torch.load("./corr_model")
    self.correction_model     = self.correction_model.to(device)
    self.model_loaded = True
    print("[Gramformer] Grammar error correct/highlight model loaded..")

    
  def correct(self, input_sentence, max_candidates=1, max_len=128):
      if self.model_loaded:
        correction_prefix = "gec: "
        input_sentence = correction_prefix + input_sentence
        input_ids = self.correction_tokenizer.encode(input_sentence, return_tensors='pt')
        input_ids = input_ids.to(self.device)

        preds = self.correction_model.generate(
            input_ids,
            do_sample=True, 
            max_length=max_len, 
            # top_k=50,
            # top_p=0.95,
            num_beams=7,
            early_stopping=True,
            num_return_sequences=max_candidates)

        corrected = set()
        for pred in preds:
          corrected.add(self.correction_tokenizer.decode(pred, skip_special_tokens=True).strip())
        return corrected
      else:
        print("Model is not loaded")
        return None

  def highlight(self, orig, cor):
      edits = self._get_edits(orig, cor)
      orig_tokens = orig.split()

      ignore_indexes = []
      for edit in edits:
          edit_type = edit[0]
          edit_str_start = edit[1]
          edit_spos = edit[2]
          edit_epos = edit[3]
          edit_str_end = edit[4]

          # if no_of_tokens(edit_str_start) > 1 ==> excluding the first token, mark all other tokens for deletion
          for i in range(edit_spos+1, edit_epos):
            ignore_indexes.append(i)

          if edit_str_start == "":
              if edit_spos - 1 >= 0:
                  new_edit_str = orig_tokens[edit_spos - 1]
                  edit_spos -= 1
              else:
                  new_edit_str = orig_tokens[edit_spos + 1]
                  edit_spos += 1
              if edit_type == "PUNCT":
                st = "<a type='" + edit_type + "' edit='" + \
                    edit_str_end + "'>" + new_edit_str + "</a>"
              else:
                st = "<a type='" + edit_type + "' edit='" + new_edit_str + \
                    " " + edit_str_end + "'>" + new_edit_str + "</a>"
              orig_tokens[edit_spos] = st
          elif edit_str_end == "":
            st = "<d type='" + edit_type + "' edit=''>" + edit_str_start + "</d>"
            orig_tokens[edit_spos] = st
          else:
            st = "<c type='" + edit_type + "' edit='" + \
                edit_str_end + "'>" + edit_str_start + "</c>"
            orig_tokens[edit_spos] = st

      for i in sorted(ignore_indexes, reverse=True):
        del(orig_tokens[i])
      return(" ".join(orig_tokens))


  def _get_edits(self, orig, cor):
        orig = self.annotator.parse(orig)
        cor = self.annotator.parse(cor)
        alignment = self.annotator.align(orig, cor)
        edits = self.annotator.merge(alignment)

        if len(edits) == 0:  
            return []

        edit_annotations = []
        for e in edits:
            e = self.annotator.classify(e)
            edit_annotations.append((e.type[2:], e.o_str, e.o_start, e.o_end,  e.c_str, e.c_start, e.c_end))
                
        if len(edit_annotations) > 0:
            return edit_annotations
        else:    
            return []

  def get_edits(self, orig, cor):
      return self._get_edits(orig, cor)